import gym
import numpy as np

from roboverse.bullet.serializable import Serializable
import roboverse.bullet as bullet

END_EFFECTOR_INDEX = 8
RESET_JOINT_VALUES = [1.57, -0.6, -0.6, 0, -1.57, 0., 0., 0.036, -0.036]
RESET_JOINT_INDICES = [0, 1, 2, 3, 4, 5, 7, 10, 11]
GUESS = 3.14  # TODO(avi) This is a guess, need to verify what joint this is
JOINT_LIMIT_LOWER = [-3.14, -1.88, -1.60, -3.14, -2.14, -3.14, -GUESS, 0.015, -0.037]
JOINT_LIMIT_UPPER = [3.14, 1.99, 2.14, 3.14, 1.74, 3.14, GUESS, 0.037, -0.015]
JOINT_RANGE = []
for upper, lower in zip(JOINT_LIMIT_LOWER, JOINT_LIMIT_UPPER):
    JOINT_RANGE.append(upper-lower)

GRIPPER_LIMITS_LOW = [0., -0.036]
GRIPPER_LIMITS_HIGH = [0.036, 0.]
GRIPPER_OPEN_STATE = [0.036, -0.036]
GRIPPER_CLOSED_STATE = [0., 0.]


class Widow250Env(gym.Env, Serializable):

    def __init__(self,
                 control_mode='continuous',
                 observation_mode='pixels',
                 observation_img_dim=48,
                 num_sim_steps=10,
                 num_sim_steps_reset=50,
                 num_sim_steps_discrete_action=75,
                 transpose_image=True,
                 gui=False,
                 ee_pos_high=(0.8, .4, -0.1),
                 ee_pos_low=(.4, -.2, -.34),
                 camera_target_pos=(0.6, 0.0, -0.4),
                 camera_distance=0.5,
                 camera_roll=0.0,
                 camera_pitch=-40,
                 camera_yaw=180,
                 use_vr=False,
                 ):

        self.control_mode = control_mode
        self.observation_mode = observation_mode
        self.observation_img_dim = observation_img_dim

        self.num_sim_steps = num_sim_steps
        self.num_sim_steps_reset = num_sim_steps_reset
        self.num_sim_steps_discrete_action = num_sim_steps_discrete_action

        self.transpose_image = transpose_image
        self.gui = gui

        # TODO(avi): Add limits to ee orientation as well
        self.ee_pos_high = ee_pos_high
        self.ee_pos_low = ee_pos_low

        self.use_vr = use_vr
        if self.use_vr:
            bullet.connect_headless_vr(self.gui)
        else:
            bullet.connect_headless(self.gui)

        self.object_position = (.65, 0.3, -.3)
        self.object_orientation = (0, 0, 0.707107, 0.707107)

        self._load_meshes()
        self.movable_joints = bullet.get_movable_joints(self.robot_id)
        self.end_effector_index = END_EFFECTOR_INDEX
        self.reset_joint_values = RESET_JOINT_VALUES
        self.reset_joint_indices = RESET_JOINT_INDICES

        self.camera_target_pos = camera_target_pos
        self.camera_distance = camera_distance
        self.camera_roll = camera_roll
        self.camera_pitch = camera_pitch
        self.camera_yaw = camera_yaw
        view_matrix_args = dict(target_pos=self.camera_target_pos,
                                distance=self.camera_distance,
                                yaw=self.camera_yaw,
                                pitch=self.camera_pitch,
                                roll=self.camera_roll,
                                up_axis_index=2)
        self._view_matrix_obs = bullet.get_view_matrix(
            **view_matrix_args)
        self._projection_matrix_obs = bullet.get_projection_matrix(
            self.observation_img_dim, self.observation_img_dim)



        self.xyz_action_scale = 1.0
        self.abc_action_scale = 20.0
        self.gripper_action_scale = 20.0

        self._set_action_space()
        self._set_observation_space()

        self.is_gripper_open = True  # TODO(avi): Clean this up

        self.reset()

    def _load_meshes(self):
        from roboverse.envs import objects
        self.table_id = objects.table()
        self.robot_id = objects.widow250()
        self.tray_id = objects.tray(base_position=self.object_position)
        # TODO(avi): Generalize this to more than one object
        self.duck_id = objects.duck()

    def reset(self):
        bullet.reset()
        bullet.setup_headless()
        self._load_meshes()
        bullet.reset_robot(
            self.robot_id,
            self.reset_joint_indices,
            self.reset_joint_values)
        self.is_gripper_open = True  # TODO(avi): Clean this up

        return self.get_observation()

    def step(self, action):
        action = np.clip(action, -1, +1)  # TODO maybe clean this up

        xyz_action = action[:3]  # ee position actions
        abc_action = action[3:6]  # ee orientation actions
        gripper_action = action[6]

        ee_pos, ee_quat = bullet.get_link_state(
            self.robot_id, self.end_effector_index)
        joint_states, _ = bullet.get_joint_states(self.robot_id,
                                                  self.movable_joints)
        gripper_state = np.asarray([joint_states[-2], joint_states[-1]])

        target_ee_pos = ee_pos + self.xyz_action_scale * xyz_action
        ee_deg = bullet.quat_to_deg(ee_quat)
        target_ee_deg = ee_deg + self.abc_action_scale * abc_action
        target_ee_quat = bullet.deg_to_quat(target_ee_deg)

        if self.control_mode == 'continuous':
            num_sim_steps = self.num_sim_steps
            target_gripper_state = gripper_state + \
                                   [-self.gripper_action_scale * gripper_action,
                                    self.gripper_action_scale * gripper_action]

        elif self.control_mode == 'discrete_gripper':
            if gripper_action > 0.5:
                num_sim_steps = self.num_sim_steps_discrete_action
                target_gripper_state = GRIPPER_OPEN_STATE
                self.is_gripper_open = True  # TODO(avi): Clean this up

            elif gripper_action < -0.5:
                num_sim_steps = self.num_sim_steps_discrete_action
                target_gripper_state = GRIPPER_CLOSED_STATE
                self.is_gripper_open = False  # TODO(avi): Clean this up
            else:
                num_sim_steps = self.num_sim_steps
                if self.is_gripper_open:
                    target_gripper_state = GRIPPER_OPEN_STATE
                else:
                    target_gripper_state = GRIPPER_CLOSED_STATE
                # target_gripper_state = gripper_state
        else:
            raise NotImplementedError

        target_ee_pos = np.clip(target_ee_pos, self.ee_pos_low, self.ee_pos_high)
        target_gripper_state = np.clip(target_gripper_state, GRIPPER_LIMITS_LOW,
                                       GRIPPER_LIMITS_HIGH)

        bullet.apply_action_ik(
            target_ee_pos, target_ee_quat, target_gripper_state,
            self.robot_id,
            self.end_effector_index, self.movable_joints,
            lower_limit=JOINT_LIMIT_LOWER,
            upper_limit=JOINT_LIMIT_UPPER,
            rest_pose=RESET_JOINT_VALUES,
            joint_range=JOINT_RANGE,
            num_sim_steps=num_sim_steps)

        info = self.get_info()
        reward = self.get_reward(info)
        done = False
        return self.get_observation(), reward, done, info

    def get_observation(self):
        gripper_state = self.get_gripper_state()
        ee_pos, ee_quat = bullet.get_link_state(
            self.robot_id, self.end_effector_index)
        if self.observation_mode == 'pixels':
            image_observation = self.render_obs()
            image_observation = np.float32(image_observation.flatten()) / 255.0
            observation = {
                'state': np.concatenate(
                    (ee_pos, ee_quat, gripper_state)),
                'image': image_observation
            }
        else:
            raise NotImplementedError

        return observation

    def get_reward(self, info):
        pass

    def get_info(self):
        pass

    def render_obs(self):
        img, depth, segmentation = bullet.render(
            self.observation_img_dim, self.observation_img_dim,
            self._view_matrix_obs, self._projection_matrix_obs, shadow=0)
        if self.transpose_image:
            img = np.transpose(img, (2, 0, 1))
        return img

    def _set_action_space(self):
        self.action_dim = 7
        act_bound = 1
        act_high = np.ones(self.action_dim) * act_bound
        self.action_space = gym.spaces.Box(-act_high, act_high)

    def _set_observation_space(self):
        if self.observation_mode == 'pixels':
            self.image_length = (self.observation_img_dim ** 2) * 3
            img_space = gym.spaces.Box(0, 1, (self.image_length,),
                                       dtype=np.float32)
            robot_state_dim = 9  # XYZ + QUAT + GRIPPER_STATE
            obs_bound = 100
            obs_high = np.ones(robot_state_dim) * obs_bound
            state_space = gym.spaces.Box(-obs_high, obs_high)
            spaces = {'image': img_space, 'state': state_space}
            self.observation_space = gym.spaces.Dict(spaces)
        else:
            raise NotImplementedError

    def get_gripper_state(self):
        joint_states, _ = bullet.get_joint_states(self.robot_id,
                                                  self.movable_joints)
        gripper_state = np.asarray(joint_states[-2:])
        return gripper_state


if __name__ == "__main__":
    env = Widow250Env(gui=True)
    import time

    for i in range(20):
        print(i)
        env.step(np.asarray([-0.05, 0., 0., 0., 0., 0.5, 0.]))
        time.sleep(0.1)

    env.reset()
    time.sleep(1)
    for _ in range(25):
        env.step(np.asarray([0., 0., 0., 0., 0., 0., 0.6]))
        time.sleep(0.1)

    env.reset()
    import IPython; IPython.embed()
