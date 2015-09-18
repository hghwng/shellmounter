#!/usr/bin/env python3
import dbus
import sys
import os
import xml.etree.ElementTree as etree
DBUS_OBJECT = 'org.freedesktop.UDisks2'
DBUS_PATH = '/org/freedesktop/UDisks2/block_devices'

g_bus = dbus.SystemBus()


def comm_get_device_info(info):
    str_info = info['label']
    if str_info == '':
        obj = g_bus.get_object(DBUS_OBJECT, path)
        iface = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')

        vendor = ''
        try:
            vendor = iface.Get(DBUS_OBJECT + '.Drive', 'Vendor')
        except dbus.exceptions.DBusException:
            pass

        model = ''
        try:
            model = iface.Get(DBUS_OBJECT + '.Drive', 'Model')
        except dbus.exceptions.DBusException:
            pass

        if vendor != '' and model != '':
            str_info = vendor + ' ' + model
        else:
            str_info = vendor + model

    str_info += '(' + util_human_size(info['size']) + ')'
    return str_info


def comm_bytes_to_str(bytes):
    return bytearray(bytes).rstrip(bytearray((0,))).decode('utf-8')


def comm_refresh_info():
    global g_blocks
    obj = g_bus.get_object(DBUS_OBJECT, DBUS_PATH)
    iface = dbus.Interface(obj, 'org.freedesktop.DBus.Introspectable')
    tree = etree.fromstring(iface.Introspect())
    blocks = [i.get('name') for i in tree]

    ret = {}
    for block in blocks:
        info = {}
        obj = g_bus.get_object(DBUS_OBJECT, DBUS_PATH + '/' + block)
        iface = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')

        namespace = DBUS_OBJECT + '.Block'
        if iface.Get(namespace, 'HintIgnore'):
            continue
        if not iface.Get(namespace, 'HintAuto'):
            continue
        if iface.Get(namespace, 'IdUsage') != 'filesystem':
            continue

        info['size'] = int(iface.Get(namespace, 'Size'))
        if info['size'] == 0:
            continue
        info['drive'] = str(iface.Get(namespace, 'Drive'))
        info['label'] = str(iface.Get(namespace, 'IdLabel'))
        info['device'] = comm_bytes_to_str(iface.Get(namespace, 'Device'))

        # Filesystem, Partition and Loop are optional
        try:
            bytes = iface.Get(DBUS_OBJECT + '.Filesystem', 'MountPoints')
            info['mountpoints'] = [comm_bytes_to_str(i) for i in bytes]
        except dbus.exceptions.DBusException:
            info['mountpoints'] = []

        try:
            path = str(iface.Get(DBUS_OBJECT + '.Partition', 'Table'))
            info['table'] = path[len(DBUS_PATH) + 1:]
        except:
            info['table'] = ''

        ret[block] = info

    g_blocks = ret


def comm_mount(block):
    try:
        obj = g_bus.get_object(DBUS_OBJECT, DBUS_PATH + '/' + block)
        array = dbus.Array(signature='s')
        path = obj.Mount(array, dbus_interface=DBUS_OBJECT + '.Filesystem')
        return {'succ': True, 'path': path}
    except dbus.exceptions.DBusException as err:
        return {'succ': False,
                'name': err.get_dbus_name().strip(),
                'msg': err.get_dbus_message().strip()}


def comm_unmount(block):
    try:
        obj = g_bus.get_object(DBUS_OBJECT, DBUS_PATH + '/' + block)
        array = dbus.Array(signature='s')
        obj.Unmount(array, dbus_interface=DBUS_OBJECT + '.Filesystem')
        return {'succ': True}
    except dbus.exceptions.DBusException as err:
        return {'succ': False,
                'name': err.get_dbus_name().strip(),
                'msg': err.get_dbus_message().strip()}


def util_human_size(size):
    unit = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']
    for i in range(len(unit)):
        if size < 1000:
            return "{0:.0f}{1}".format(size, unit[i])
        size /= 1000


def util_quote(string):
    # "ao'ue" -> 'ao' "'" 'ue'
    parts = string.split("'")
    for i in range(len(parts)):
        parts[i] = "'" + parts[i] + "'"
    return '"\'"'.join(parts)


def util_print_complete_string(opts):
    parts = []
    for i in opts:
        parts.append(util_quote(i[0].replace(':', '\:') + ':' +
                                i[1].replace(':', '\:')))
    print('args=(' + ' '.join(parts) + ');')


def util_message(*kwargs):
    print(*kwargs, file=sys.stderr)


def util_exec(*kwargs):
    print(' '.join(kwargs) + ';')


def cmd_complete_block(already_mounted):
    args = []

    tables = {}
    for block, info in g_blocks.items():
        if bool(len(info['mountpoints'])) != already_mounted:
            continue

        str_info = comm_get_device_info(info)
        args.append([info['device'], str_info])
        if info['label']:
            args.append([info['label'], info['device']])
        for i in info['mountpoints']:
            args.append([i, str_info])

        if info['table'] not in tables:
            tables[info['table']] = [str_info]
        else:
            tables[info['table']].append(str_info)

    for table, info_list in tables.items():
        info_str = ', '.join(info_list)
        args.append(['/dev/' + table, info_str])

    util_print_complete_string(args)


def util_match_block(args):
    if len(args) == 0:
        # Select all block device
        oplist = []
        for block, info in g_blocks.items():
            oplist.append(block)
        return oplist

    import os.path
    oplist = set()

    for block, info in g_blocks.items():
        for arg in args:
            if '/dev/' + info['table'] == arg:
                oplist.add(block)
            elif info['device'] == arg:
                oplist.add(block)
            elif info['label'] == arg:
                oplist.add(block)
            else:
                for i in info['mountpoints']:
                    if os.path.abspath(i) == os.path.abspath(arg):
                        oplist.add(block)

    return list(oplist)


def cmd_mount(oplist):
    global g_cwd
    completed = []
    for block in oplist:
        ret = comm_mount(block)
        if not ret['succ']:
            util_message('error({0}): {1}'.format(block, ret['msg']))
        else:
            completed.append(ret['path'])

    if len(completed) == 0:
        return
    elif len(completed) == 1:
        g_cwd = completed[0]
    else:
        util_message('Info: Multiple directories mounted:')
        for i in completed:
            util_message('\t' + i)
        g_cwd = os.path.commonprefix(completed)


def cmd_toggle(args):
    mounted = []
    unmounted = []
    blocks = util_match_block(args)
    for block in blocks:
        if len(g_blocks[block]['mountpoints']):
            mounted.append(block)
        else:
            unmounted.append(block)

    if len(args) == 0:
        # First try to mount anything mountable
        # If nothing mountable, unmount everything mountable
        if len(unmounted) == 0:
            util_message('Info: unmounting ' + ' '.join(mounted))
            cmd_unmount(mounted)
        else:
            util_message('Info: mounting ' + ' '.join(unmounted))
            cmd_mount(unmounted)
    else:
        # Only allow same type operation
        if len(mounted) and len(unmounted):
            util_message('Error: blocks to operate should be all mounted'
                         'or unmounted.')
            util_message('\tMounted: ' + ' '.join(mounted))
            util_message('\tUnmounted: ' + ' '.join(unmounted))
        else:
            if len(mounted):
                util_message('Info: unmounting ' + ' '.join(blocks))
                cmd_unmount(blocks)
            elif len(unmounted):
                util_message('Info: mounting ' + ' '.join(blocks))
                cmd_mount(blocks)


def cmd_unmount(oplist):
    # cd to parent if g_cwd is inside mountpoints being unmounted
    global g_cwd
    for block in oplist:
        for i in g_blocks[block]['mountpoints']:
            if g_cwd.startswith(i):
                g_cwd = os.path.dirname(i)

    used_dirs = []
    for block in oplist:
        ret = comm_unmount(block)
        if not ret['succ']:
            util_message('Error({0}): {1}'.format(block, ret['msg']))
            if ret['name'] == 'org.freedesktop.UDisks2.Error.DeviceBusy':
                used_dirs.extend(g_blocks[block]['mountpoints'])

    # On device busy errors, show device usage
    if len(used_dirs):
        util_exec('lsof ' + ' '.join((util_quote(i) for i in used_dirs)))

    # XXX power off


def cmd_status():
    for block, info in g_blocks.items():
        mount_sign = '*' if len(info['mountpoints']) else ' '
        misc_info = comm_get_device_info(info)
        util_message('{0} {1}\t{2}'.format(mount_sign, block, misc_info))


def cmd_help():
    util_message('''
Usage: shellmounter {toggle,mount,unmount} [DEVICE]...
       shellmounter complete {mount,unmount}'
       shellmounter status
       shellmounter help

toggle      toggle between mounted or unmounted
mount       mount by partition, disk, or label
unmount     mount by partition, disk, label or mount point
status      show statuts of managed partitions
complete    build variable for shell completion
''')


def main():
    comm_refresh_info()

    if len(sys.argv) <= 1:
        return cmd_help()

    fn = {'status': cmd_status, 'help': cmd_help}.get(sys.argv[1])
    if fn and len(sys.argv) == 2:
        return fn()

    fn = {'mount': lambda args: cmd_mount(util_match_block(args)),
          'unmount': lambda args: cmd_unmount(util_match_block(args)),
          'toggle': lambda args: cmd_toggle(args)}.get(sys.argv[1])
    if fn:
        return fn(sys.argv[2:])

    if sys.argv[1] == 'complete':
        if sys.argv[2] == 'mount':
            return cmd_complete_block(False)
        elif sys.argv[2] == 'unmount':
            return cmd_complete_block(True)

    return cmd_help()

if __name__ == '__main__':
    g_cwd = os.getenv('OLDPWD')
    main()
    util_exec('PWD=' + util_quote(g_cwd))
