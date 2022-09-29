
import pytest
import sys

if sys.version_info[0] < 3:
    pytest.skip("skipping Tesseract tests on Python 2", allow_module_level=True)

import general_robotics_toolbox as rox
import numpy as np
import numpy.testing as nptest
import os

tesseract_common = pytest.importorskip('tesseract_robotics.tesseract_common')

from general_robotics_toolbox import tesseract as rox_tesseract
from general_robotics_toolbox import robotraconteur as rr_rox

from tesseract_robotics.tesseract_scene_graph import \
    JointType_FIXED, JointType_REVOLUTE, JointType_PRISMATIC
from tesseract_robotics.tesseract_environment import Environment
from tesseract_robotics.tesseract_common import TransformMap, Isometry3d
from tesseract_robotics.tesseract_kinematics import KinGroupIKInput, KinGroupIKInputs

def _assert_rox_eig_transform_close(T, eig_iso):
    H_eig_iso = eig_iso.matrix()
    H_T = np.zeros((4,4),dtype=np.float64)
    H_T[0:3,0:3] = T.R
    H_T[0:3,3] = T.p
    H_T[3,3] = 1.0

    nptest.assert_allclose(H_eig_iso, H_T, atol = 1e-4)

def test_transform_to_isometry3d():
    T = rox.random_transform()
    eig_iso = rox_tesseract._transform_to_isometry3d(T)
    _assert_rox_eig_transform_close(T, eig_iso)

def test_get_fixed_link_command():
    T = rox.random_transform()
    link, joint = rox_tesseract._get_fixed_link_and_joint(T, "my_link", "my_joint", "my_parent_link")
    assert link.getName() == "my_link"
    assert joint.parent_link_name == "my_parent_link"
    assert joint.child_link_name == "my_link"
    assert joint.getName() == "my_joint"
    _assert_rox_eig_transform_close(T, joint.parent_to_joint_origin_transform)

def test_get_link_command():
    p = rox.random_p()
    h = rox.random_p()
    h = h/np.linalg.norm(h)

    link, joint = rox_tesseract._get_link_and_joint(h, p, 0, -np.rad2deg(24), np.rad2deg(34),
        7.92, 8.92, 6.432, "my_link4", "my_joint8", "my_link3")

    assert link.getName() == "my_link4"
    assert joint.parent_link_name == "my_link3"
    assert joint.child_link_name == "my_link4"
    assert joint.getName() == "my_joint8"
    _assert_rox_eig_transform_close(rox.Transform(np.eye(3),p), 
        joint.parent_to_joint_origin_transform)
    nptest.assert_allclose(h, joint.axis.flatten(), atol=1e-6)
    assert joint.type == JointType_REVOLUTE

    limits = joint.limits
    assert limits.lower == -np.rad2deg(24)
    assert limits.upper == np.rad2deg(34)
    assert limits.velocity == 7.92
    assert limits.acceleration == 8.92
    assert limits.effort == 6.432

def _get_absolute_path(fname):
    dirname = os.path.dirname(os.path.realpath(__file__))
    return dirname + "/" + fname

def _assert_sg_joint(sg_joint, name, parent, child, sg_type, h, p, l, u, v, a):
    assert sg_joint.getName() == name
    assert sg_joint.parent_link_name == parent
    assert sg_joint.child_link_name == child
    assert sg_joint.type == sg_type
    sg_limits = sg_joint.limits
    assert sg_limits.lower == l
    assert sg_limits.upper == u
    assert sg_limits.velocity == v
    assert sg_limits.acceleration == a

    _assert_rox_eig_transform_close(rox.Transform(np.eye(3),p), 
        sg_joint.parent_to_joint_origin_transform)
    nptest.assert_allclose(h, sg_joint.axis.flatten(), atol=1e-5)
    
def _assert_sg_fixed_joint(sg_joint, name, parent, child, q, p):
    assert sg_joint.getName() == name
    assert sg_joint.parent_link_name == parent
    assert sg_joint.child_link_name == child
    assert sg_joint.type == JointType_FIXED
    T = rox.Transform(rox.q2R(q),p)
    _assert_rox_eig_transform_close(T, sg_joint.parent_to_joint_origin_transform)

def test_robot_to_scene_graph_sawyer():
    with open(_get_absolute_path("sawyer_robot_with_electric_gripper_config.yml"), "r") as f:
        robot = rr_rox.load_robot_info_yaml_to_robot(f)

    sg, link_names, joint_names, chain_link_names = rox_tesseract.robot_to_scene_graph(robot, True)

    assert link_names == ['base_link', 'link_1', 'link_2', 'link_3', 'link_4', 'link_5', 'link_6', 'link_7',
     'chain_tip', 'flange', 'tool_tcp']
         
    assert joint_names ==  ['right_j0', 'right_j1', 'right_j2', 'right_j3', 'right_j4', 'right_j5', 'right_j6']
    assert chain_link_names == ['base_link', 'link_1', 'link_2', 'link_3', 'link_4', 'link_5', 'link_6', 'link_7']

    sg_links_v = sg.getLinks()
    sg_joints_v = sg.getJoints()
    sg_links = {sg_links_v[i].getName(): sg_links_v[i] for i in range(len(sg_links_v))}
    sg_joints = {sg_joints_v[i].getName(): sg_joints_v[i] for i in range(len(sg_joints_v))}

    assert set(sg_links.keys()) == set(['link_1', 'base_link', 'link_2', 'link_3', 'link_4', 'link_5', 'link_6', 
        'link_7', 'chain_tip', 'flange', 'tool_tcp'])
    assert set(sg_joints.keys()) == set(['right_j0', 'right_j1', 'right_j2', 'link_7_to_chain_tip',
         'right_j3', 'right_j4', 'right_j5', 'right_j6', 'tip_to_flange', 'tip_to_tool'])

    _assert_sg_joint(sg_joints["right_j0"], "right_j0", "base_link", "link_1", JointType_REVOLUTE, 
    [0,0,1], [0,0,0.08], -3.0503, 3.0503, 1.74, 3.5)
    _assert_sg_joint(sg_joints["right_j1"], "right_j1", "link_1", "link_2", JointType_REVOLUTE, 
    [0,1,0], [0.081,0.05,0.237], -3.8095, 2.2736, 1.328, 2.5)
    _assert_sg_joint(sg_joints["right_j2"], "right_j2", "link_2", "link_3", JointType_REVOLUTE, 
    [1,0,0], [0.14,0.1425,0], -3.0426, 3.0426, 1.957, 5.0)
    _assert_sg_joint(sg_joints["right_j3"], "right_j3", "link_3", "link_4", JointType_REVOLUTE, 
    [0,1,0], [0.26,-0.042,0], -3.0439, 3.0439, 1.957, 5.0)
    _assert_sg_joint(sg_joints["right_j4"], "right_j4", "link_4", "link_5", JointType_REVOLUTE, 
    [1,0,0], [0.125,-0.1265,0], -2.9761, 2.9761, 3.485, 5.0)
    _assert_sg_joint(sg_joints["right_j5"], "right_j5", "link_5", "link_6", JointType_REVOLUTE, 
    [0,1,0], [0.275,0.031,0], -2.9761, 2.9761, 3.485, 5.0)
    _assert_sg_joint(sg_joints["right_j6"], "right_j6", "link_6", "link_7", JointType_REVOLUTE, 
    [1,0,0], [0.11,0.1053,0], -4.7124, 4.7124, 4.545, 5.0)
    _assert_sg_fixed_joint(sg_joints["link_7_to_chain_tip"], "link_7_to_chain_tip", "link_7", "chain_tip", \
        [1,0,0,0], [0.0245,0,0])
    _assert_sg_fixed_joint(sg_joints["tip_to_flange"], "tip_to_flange", "chain_tip", "flange", \
        [-0.454518, 0.541676, -0.454521, 0.541672], [0,0,0])
    _assert_sg_fixed_joint(sg_joints["tip_to_tool"], "tip_to_tool", "flange", "tool_tcp", \
        [0.999048, 0, 0, 0.043619], [0,0,0.1577])

def test_robot_to_tesseract_env_commands_and_kin_sawyer():
    with open(_get_absolute_path("sawyer_robot_with_electric_gripper_config.yml"), "r") as f:
        robot = rr_rox.load_robot_info_yaml_to_robot(f)

    tesseract_env_commands = rox_tesseract.robot_to_tesseract_env_commands(robot, "sawyer")
    env = Environment()
    assert env.init(tesseract_env_commands)

    # kin_info = env.getKinematicsInformation()
    kin_group = env.getKinematicGroup("sawyer")
    kin_group_joint_names = kin_group.getJointNames()
    kin_group_link_names = kin_group.getLinkNames()


    assert set(kin_group_joint_names) == set(['sawyer_right_j0', 'sawyer_right_j1', 'sawyer_right_j2', 'sawyer_right_j3', 
        'sawyer_right_j4', 'sawyer_right_j5', 'sawyer_right_j6'])

    assert set(kin_group_link_names) == set(['sawyer_link_5', 'sawyer_base_link', 'world', 'sawyer_link_1', 
        'sawyer_link_0', 'sawyer_link_2', 'sawyer_link_3', 'sawyer_link_4', 'sawyer_link_6', 'sawyer_link_7',
        'sawyer_flange', 'sawyer_tool_tcp'])

    q = np.ones((7,),dtype=np.float64)*np.deg2rad(15)
    tcp_pose = kin_group.calcFwdKin(q)["sawyer_tool_tcp"]
    
    ik = KinGroupIKInput()
    ik.pose = tcp_pose
    ik.tip_link_name = "sawyer_tool_tcp"
    ik.working_frame = "world"
    iks = KinGroupIKInputs()
    iks.append(ik)

    invkin1 = kin_group.calcInvKin(iks,q*0.7)

    nptest.assert_allclose(q, invkin1[0].flatten(), atol=np.deg2rad(0.5))


def test_kinematics_plugin_info_string_sawyer():
    with open(_get_absolute_path("sawyer_robot_with_electric_gripper_config.yml"), "r") as f:
        robot = rr_rox.load_robot_info_yaml_to_robot(f)

    sg, link_names, joint_names, chain_link_names = rox_tesseract.robot_to_scene_graph(robot,True)

    kin_plugin_info = rox_tesseract.kinematics_plugin_info_string(robot, "my_robot", link_names, joint_names, chain_link_names,
        "KDLInvKinChainNR")

    kin_plugin_info_expected = 'kinematic_plugins:\n  fwd_kin_plugins:\n    my_robot:\n      default: KDLFwdKinChain\n' \
    '      plugins:\n        KDLFwdKinChain:\n          class: KDLFwdKinChainFactory\n          config:\n' \
    '            base_link: base_link\n            tip_link: tool_tcp\n  inv_kin_plugins:\n    my_robot:\n' \
    '      default: KDLInvKinChainNR\n      plugins:\n        KDLInvKinChainLMA:\n' \
    '          class: KDLInvKinChainLMAFactory\n          config:\n            base_link: link_0\n' \
    '            tip_link: link_7\n        KDLInvKinChainNR:\n          class: KDLInvKinChainNRFactory\n' \
    '          config:\n            base_link: link_0\n            tip_link: link_7\n  search_libraries:\n' \
    '  - tesseract_kinematics_kdl_factories\n'

    assert kin_plugin_info == kin_plugin_info_expected