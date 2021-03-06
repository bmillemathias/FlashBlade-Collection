#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: purefb_fs
version_added: "2.6"
short_description:  Manage filesystemon Pure Storage FlashBlade`
description:
    - This module manages filesystems on Pure Storage FlashBlade.
author: Pure Storage Ansible Team (@sdodsley) <pure-ansible-team@purestorage.com>
options:
  name:
    description:
      - Filesystem Name.
    required: true
    type: str
  state:
    description:
      - Create, delete or modifies a filesystem.
    required: false
    default: present
    type: str
    choices: [ "present", "absent" ]
  eradicate:
    description:
      - Define whether to eradicate the filesystem on delete or leave in trash.
    required: false
    type: bool
    default: false
  size:
    description:
      - Volume size in M, G, T or P units. See examples.
      - If size is not set at filesystem creation time it defaults to 32G
    type: str
    required: false
  nfsv3:
    description:
      - Define whether to NFSv3 protocol is enabled for the filesystem.
    required: false
    type: bool
    default: true
    version_added: 2.9
  nfsv4:
    description:
      - Define whether to NFSv4.1 protocol is enabled for the filesystem.
    required: false
    type: bool
    default: true
    version_added: 2.9
  nfs_rules:
    description:
      - Define the NFS rules in operation.
      - If not set at filesystem creation time it defaults to I(*(rw,no_root_squash))
      - Supported binary options are ro/rw, secure/insecure, fileid_32bit/no_fileid_32bit,
        root_squash/no_root_squash, all_squash/no_all_squash and atime/noatime
      - Supported non-binary options are anonuid=#, anongid=#, sec=(sys|krb5)
    required: false
    type: str
  smb:
    description:
      - Define whether to SMB protocol is enabled for the filesystem.
    required: false
    type: bool
    default: false
  smb_aclmode:
    description:
      - Specify the ACL mode for the SMB protocol.
    required: false
    type: str
    default: shared
    choices: [ "shared", "native" ]
  http:
    description:
      - Define whether to HTTP/HTTPS protocol is enabled for the filesystem.
    required: false
    type: bool
    default: false
  snapshot:
    description:
      - Define whether a snapshot directory is enabled for the filesystem.
    required: false
    type: bool
    default: false
  writable:
    description:
      - Define if a filesystem is writeable.
    required: false
    type: bool
  promote:
    description:
      - Promote/demote a filesystem.
      - Can only demote the file-system if it is in a replica-link relationship.
    required: false
    type: bool
  fastremove:
    description:
      - Define whether the fast remove directory is enabled for the filesystem.
    required: false
    type: bool
    default: false
  hard_limit:
    description:
      - Define whether the capacity for a filesystem is a hard limit.
      - CAUTION This will cause the filesystem to go Read-Only if the
        capacity has already exceeded the logical size of the filesystem.
    required: false
    type: bool
    default: false
    version_added: 2.8
  user_quota:
    description:
      - Default quota in M, G, T or P units for a user under this file system.
    required: false
    type: str
    version_added: 2.9
  group_quota:
    description:
      - Default quota in M, G, T or P units for a group under this file system.
    required: false
    type: str
    version_added: 2.9
  policy:
    description:
      - Filesystem policy to assign to or remove from a filesystem.
    required: false
    type: str
  policy_state:
    description:
    - Add or delete a policy from a filesystem
    required: false
    default: present
    type: str
    choices: [ "absent", "present" ]
extends_documentation_fragment:
    - purestorage.flashblade.purestorage.fb
'''

EXAMPLES = '''
- name: Create new filesystem named foo
  purefb_fs:
    name: foo
    size: 1T
    state: present
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Delete filesystem named foo
  purefb_fs:
    name: foo
    state: absent
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Recover filesystem named foo
  purefb_fs:
    name: foo
    state: present
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Eradicate filesystem named foo
  purefb_fs:
    name: foo
    state: absent
    eradicate: true
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Promote filesystem named foo ready for failover
  purefb_fs:
    name: foo
    promote: true
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Demote filesystem named foo after failover
  purefb_fs:
    name: foo
    promote: false
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641

- name: Modify attributes of an existing filesystem named foo
  purefb_fs:
    name: foo
    size: 2T
    nfsv3 : false
    nfsv4 : true
    user_quota: 10K
    group_quota: 25M
    nfs_rules: '10.21.200.0/24(ro)'
    snapshot: true
    fastremove: true
    hard_limit: true
    smb: true
    state: present
    fb_url: 10.10.10.2
    api_token: T-55a68eb5-c785-4720-a2ca-8b03903bf641'''

RETURN = '''
'''

HAS_PURITY_FB = True
try:
    from purity_fb import FileSystem, ProtocolRule, NfsRule, SmbRule
except ImportError:
    HAS_PURITY_FB = False

from ansible.module_utils.basic import AnsibleModule, human_to_bytes
from ansible_collections.purestorage.flashblade.plugins.module_utils.purefb import get_blade, purefb_argument_spec


HARD_LIMIT_API_VERSION = '1.4'
NFSV4_API_VERSION = '1.6'
REPLICATION_API_VERSION = '1.9'


def get_fs(module, blade):
    """Return Filesystem or None"""
    fsys = []
    fsys.append(module.params['name'])
    try:
        res = blade.file_systems.list_file_systems(names=fsys)
        return res.items[0]
    except Exception:
        return None


def create_fs(module, blade):
    """Create Filesystem"""
    changed = True
    if not module.check_mode:
        try:
            if not module.params['nfs_rules']:
                module.params['nfs_rules'] = '*(rw,no_root_squash)'
            if not module.params['size']:
                module.params['size'] = '32G'

            size = human_to_bytes(module.params['size'])

            if module.params['user_quota']:
                user_quota = human_to_bytes(module.params['user_quota'])
            else:
                user_quota = None
            if module.params['group_quota']:
                group_quota = human_to_bytes(module.params['group_quota'])
            else:
                group_quota = None

            api_version = blade.api_version.list_versions().versions
            if HARD_LIMIT_API_VERSION in api_version:
                if NFSV4_API_VERSION in api_version:
                    if REPLICATION_API_VERSION in api_version:
                        fs_obj = FileSystem(name=module.params['name'],
                                            provisioned=size,
                                            fast_remove_directory_enabled=module.params['fastremove'],
                                            hard_limit_enabled=module.params['hard_limit'],
                                            snapshot_directory_enabled=module.params['snapshot'],
                                            nfs=NfsRule(v3_enabled=module.params['nfsv3'],
                                                        v4_1_enabled=module.params['nfsv4'],
                                                        rules=module.params['nfs_rules']),
                                            smb=SmbRule(enabled=module.params['smb'],
                                                        acl_mode=module.params['smb_aclmode']),
                                            http=ProtocolRule(enabled=module.params['http']),
                                            default_user_quota=user_quota,
                                            default_group_quota=group_quota
                                            )
                    else:
                        fs_obj = FileSystem(name=module.params['name'],
                                            provisioned=size,
                                            fast_remove_directory_enabled=module.params['fastremove'],
                                            hard_limit_enabled=module.params['hard_limit'],
                                            snapshot_directory_enabled=module.params['snapshot'],
                                            nfs=NfsRule(v3_enabled=module.params['nfsv3'],
                                                        v4_1_enabled=module.params['nfsv4'],
                                                        rules=module.params['nfs_rules']),
                                            smb=ProtocolRule(enabled=module.params['smb']),
                                            http=ProtocolRule(enabled=module.params['http']),
                                            default_user_quota=user_quota,
                                            default_group_quota=group_quota
                                            )
                else:
                    fs_obj = FileSystem(name=module.params['name'],
                                        provisioned=size,
                                        fast_remove_directory_enabled=module.params['fastremove'],
                                        hard_limit_enabled=module.params['hard_limit'],
                                        snapshot_directory_enabled=module.params['snapshot'],
                                        nfs=NfsRule(enabled=module.params['nfsv3'], rules=module.params['nfs_rules']),
                                        smb=ProtocolRule(enabled=module.params['smb']),
                                        http=ProtocolRule(enabled=module.params['http'])
                                        )
            else:
                fs_obj = FileSystem(name=module.params['name'],
                                    provisioned=size,
                                    fast_remove_directory_enabled=module.params['fastremove'],
                                    snapshot_directory_enabled=module.params['snapshot'],
                                    nfs=NfsRule(enabled=module.params['nfs'], rules=module.params['nfs_rules']),
                                    smb=ProtocolRule(enabled=module.params['smb']),
                                    http=ProtocolRule(enabled=module.params['http'])
                                    )
            blade.file_systems.create_file_systems(fs_obj)
        except Exception:
            module.fail_json(msg="Failed to create filesystem {0}.".format(module.params['name']))
        if REPLICATION_API_VERSION in api_version:
            if module.params['policy']:
                try:
                    blade.policies.list_policies(names=[module.params['policy']])
                except Exception:
                    _delete_fs(module, blade)
                    module.fail_json(msg="Policy {0} doesn't exist.".format(module.params['policy']))
                try:
                    blade.policies.create_policy_filesystems(policy_names=[module.params['policy']],
                                                             member_names=[module.params['name']])
                except Exception:
                    _delete_fs(module, blade)
                    module.fail_json(msg="Failed to apply policy {0} when creating filesystem {1}.".format(module.params['policy'],
                                                                                                           module.params['name']))
    module.exit_json(changed=changed)


def modify_fs(module, blade):
    """Modify Filesystem"""
    changed = True
    if not module.check_mode:
        changed = False
        mod_fs = False
        attr = {}
        if module.params['policy'] and module.params['policy_state'] == 'present':
            try:
                policy = blade.policies.list_policy_filesystems(policy_names=[module.params['policy']],
                                                                member_names=[module.params['name']])
            except Exception:
                module.fail_json(msg='Policy {0} does not exist.'.format(module.params['policy']))
            if not policy.items:
                try:
                    blade.policies.create_policy_filesystems(policy_names=[module.params['policy']],
                                                             member_names=[module.params['name']])
                    mod_fs = True
                except Exception:
                    module.fail_json(msg='Failed to add filesystem {0} to policy {1}.'.format(module.params['name'],
                                                                                              module.params['polict']))
        if module.params['policy'] and module.params['policy_state'] == 'absent':
            try:
                policy = blade.policies.list_policy_filesystems(policy_names=[module.params['policy']],
                                                                member_names=[module.params['name']])
            except Exception:
                module.fail_json(msg='Policy {0} does not exist.'.format(module.params['policy']))
            if len(policy.items) == 1:
                try:
                    blade.policies.delete_policy_filesystems(policy_names=[module.params['policy']],
                                                             member_names=[module.params['name']])
                    mod_fs = True
                except Exception:
                    module.fail_json(msg='Failed to remove filesystem {0} to policy {1}.'.format(module.params['name'],
                                                                                                 module.params['polict']))
        if module.params['user_quota']:
            user_quota = human_to_bytes(module.params['user_quota'])
        if module.params['group_quota']:
            group_quota = human_to_bytes(module.params['group_quota'])
        fsys = get_fs(module, blade)
        if fsys.destroyed:
            attr['destroyed'] = False
            mod_fs = True
        if module.params['size']:
            if human_to_bytes(module.params['size']) != fsys.provisioned:
                attr['provisioned'] = human_to_bytes(module.params['size'])
                mod_fs = True
        api_version = blade.api_version.list_versions().versions
        if NFSV4_API_VERSION in api_version:
            if module.params['nfsv3'] and not fsys.nfs.v3_enabled:
                attr['nfs'] = NfsRule(v3_enabled=module.params['nfsv3'])
                mod_fs = True
            if not module.params['nfsv3'] and fsys.nfs.v3_enabled:
                attr['nfs'] = NfsRule(v3_enabled=module.params['nfsv3'])
                mod_fs = True
            if module.params['nfsv4'] and not fsys.nfs.v4_1_enabled:
                attr['nfs'] = NfsRule(v4_1_enabled=module.params['nfsv4'])
                mod_fs = True
            if not module.params['nfsv4'] and fsys.nfs.v4_1_enabled:
                attr['nfs'] = NfsRule(v4_1_enabled=module.params['nfsv4'])
                mod_fs = True
            if module.params['nfsv3'] or module.params['nfsv4'] and fsys.nfs.v3_enabled or fsys.nfs.v4_1_enabled:
                if module.params['nfs_rules'] is not None:
                    if fsys.nfs.rules != module.params['nfs_rules']:
                        attr['nfs'] = NfsRule(rules=module.params['nfs_rules'])
                        mod_fs = True
            if module.params['user_quota'] and user_quota != fsys.default_user_quota:
                attr['default_user_quota'] = user_quota
                mod_fs = True
            if module.params['group_quota'] and group_quota != fsys.default_group_quota:
                attr['default_group_quota'] = group_quota
                mod_fs = True
        else:
            if module.params['nfsv3'] and not fsys.nfs.enabled:
                attr['nfs'] = NfsRule(enabled=module.params['nfsv3'])
                mod_fs = True
            if not module.params['nfsv3'] and fsys.nfs.enabled:
                attr['nfs'] = NfsRule(enabled=module.params['nfsv3'])
                mod_fs = True
            if module.params['nfsv3'] and fsys.nfs.enabled:
                if fsys.nfs.rules != module.params['nfs_rules']:
                    attr['nfs'] = NfsRule(rules=module.params['nfs_rules'])
                    mod_fs = True
        if REPLICATION_API_VERSION in api_version:
            if module.params['smb'] and not fsys.smb.enabled:
                attr['smb'] = SmbRule(enabled=module.params['smb'],
                                      acl_mode=module.params['smb_aclmode'])
                mod_fs = True
            if not module.params['smb'] and fsys.smb.enabled:
                attr['smb'] = ProtocolRule(enabled=module.params['smb'])
                mod_fs = True
            if module.params['smb'] and fsys.smb.enabled:
                if fsys.smb.acl_mode != module.params['smb_aclmode']:
                    attr['smb'] = SmbRule(enabled=module.params['smb'],
                                          acl_mode=module.params['smb_aclmode'])
                    mod_fs = True
        else:
            if module.params['smb'] and not fsys.smb.enabled:
                attr['smb'] = ProtocolRule(enabled=module.params['smb'])
                mod_fs = True
            if not module.params['smb'] and fsys.smb.enabled:
                attr['smb'] = ProtocolRule(enabled=module.params['smb'])
                mod_fs = True
        if module.params['http'] and not fsys.http.enabled:
            attr['http'] = ProtocolRule(enabled=module.params['http'])
            mod_fs = True
        if not module.params['http'] and fsys.http.enabled:
            attr['http'] = ProtocolRule(enabled=module.params['http'])
            mod_fs = True
        if module.params['snapshot'] and not fsys.snapshot_directory_enabled:
            attr['snapshot_directory_enabled'] = module.params['snapshot']
            mod_fs = True
        if not module.params['snapshot'] and fsys.snapshot_directory_enabled:
            attr['snapshot_directory_enabled'] = module.params['snapshot']
            mod_fs = True
        if module.params['fastremove'] and not fsys.fast_remove_directory_enabled:
            attr['fast_remove_directory_enabled'] = module.params['fastremove']
            mod_fs = True
        if not module.params['fastremove'] and fsys.fast_remove_directory_enabled:
            attr['fast_remove_directory_enabled'] = module.params['fastremove']
            mod_fs = True
        if HARD_LIMIT_API_VERSION in api_version:
            if not module.params['hard_limit'] and fsys.hard_limit_enabled:
                attr['hard_limit_enabled'] = module.params['hard_limit']
                mod_fs = True
            if module.params['hard_limit'] and not fsys.hard_limit_enabled:
                attr['hard_limit_enabled'] = module.params['hard_limit']
                mod_fs = True
        if REPLICATION_API_VERSION in api_version:
            if module.params['writable'] is not None:
                if not module.params['writable'] and fsys.writable:
                    attr['writable'] = module.params['writable']
                    mod_fs = True
                if module.params['writable'] and not fsys.writable and fsys.promotion_status == 'promoted':
                    attr['writable'] = module.params['writable']
                    mod_fs = True
            if module.params['promote'] is not None:
                if module.params['promote'] and fsys.promotion_status != 'promoted':
                    attr['requested_promotion_state'] = 'promoted'
                    mod_fs = True
                if not module.params['promote'] and fsys.promotion_status == 'promoted':
                    # Demotion only allowed on filesystems in a replica-link
                    try:
                        blade.file_system_replica_links.list_file_system_replica_links(local_file_system_names=[module.params['name']]).items[0]
                    except Exception:
                        module.fail_json(msg='Filesystem {0} not demoted. Not in a replica-link'.format(module.params['name']))
                    attr['requested_promotion_state'] = module.params['promote']
                    mod_fs = True
        if mod_fs:
            n_attr = FileSystem(**attr)
            try:
                blade.file_systems.update_file_systems(name=module.params['name'], attributes=n_attr)
                changed = True
            except Exception:
                module.fail_json(msg="Failed to update filesystem {0}.".format(module.params['name']))
    module.exit_json(changed=changed)


def _delete_fs(module, blade):
    """ In module Delete Filesystem"""
    api_version = blade.api_version.list_versions().versions
    if NFSV4_API_VERSION in api_version:
        blade.file_systems.update_file_systems(name=module.params['name'],
                                               attributes=FileSystem(nfs=NfsRule(v3_enabled=False,
                                                                                 v4_1_enabled=False),
                                                                     smb=ProtocolRule(enabled=False),
                                                                     http=ProtocolRule(enabled=False),
                                                                     destroyed=True)
                                               )
    else:
        blade.file_systems.update_file_systems(name=module.params['name'],
                                               attributes=FileSystem(nfs=NfsRule(enabled=False),
                                                                     smb=ProtocolRule(enabled=False),
                                                                     http=ProtocolRule(enabled=False),
                                                                     destroyed=True)
                                               )

    blade.file_systems.delete_file_systems(module.params['name'])


def delete_fs(module, blade):
    """ Delete Filesystem"""
    changed = True
    if not module.check_mode:
        try:
            api_version = blade.api_version.list_versions().versions
            if NFSV4_API_VERSION in api_version:
                blade.file_systems.update_file_systems(name=module.params['name'],
                                                       attributes=FileSystem(nfs=NfsRule(v3_enabled=False,
                                                                                         v4_1_enabled=False),
                                                                             smb=ProtocolRule(enabled=False),
                                                                             http=ProtocolRule(enabled=False),
                                                                             destroyed=True)
                                                       )
            else:
                blade.file_systems.update_file_systems(name=module.params['name'],
                                                       attributes=FileSystem(nfs=NfsRule(enabled=False),
                                                                             smb=ProtocolRule(enabled=False),
                                                                             http=ProtocolRule(enabled=False),
                                                                             destroyed=True)
                                                       )

            if module.params['eradicate']:
                try:
                    blade.file_systems.delete_file_systems(module.params['name'])
                except Exception:
                    module.fail_json(msg="Failed to delete filesystem {0}.".format(module.params['name']))
        except Exception:
            module.fail_json(msg="Failed to update filesystem {0} prior to deletion.".format(module.params['name']))
    module.exit_json(changed=changed)


def eradicate_fs(module, blade):
    """ Eradicate Filesystem"""
    changed = True
    if not module.check_mode:
        try:
            blade.file_systems.delete_file_systems(module.params['name'])
        except Exception:
            module.fail_json(msg="Failed to eradicate filesystem {0}.".format(module.params['name']))
    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(
        dict(
            name=dict(type='str', required=True),
            eradicate=dict(default='false', type='bool'),
            nfsv3=dict(default='true', type='bool'),
            nfsv4=dict(default='true', type='bool'),
            nfs_rules=dict(type='str'),
            smb=dict(default='false', type='bool'),
            http=dict(default='false', type='bool'),
            snapshot=dict(default='false', type='bool'),
            writable=dict(type='bool'),
            promote=dict(type='bool'),
            fastremove=dict(default='false', type='bool'),
            hard_limit=dict(default='false', type='bool'),
            user_quota=dict(type='str'),
            policy=dict(type='str'),
            group_quota=dict(type='str'),
            smb_aclmode=dict(type='str', default='shared', choices=['shared', 'native']),
            policy_state=dict(default='present', choices=['present', 'absent']),
            state=dict(default='present', choices=['present', 'absent']),
            size=dict(type='str')
        )
    )

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True)

    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb sdk is required for this module')

    state = module.params['state']
    blade = get_blade(module)
    fsys = get_fs(module, blade)

    if state == 'present' and not fsys:
        create_fs(module, blade)
    elif state == 'present' and fsys:
        modify_fs(module, blade)
    elif state == 'absent' and fsys and not fsys.destroyed:
        delete_fs(module, blade)
    elif state == 'absent' and fsys and fsys.destroyed and module.params['eradicate']:
        eradicate_fs(module, blade)
    elif state == 'absent' and not fsys:
        module.exit_json(changed=False)
    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
