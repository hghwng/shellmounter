# Shellmounter
![demo](http://i.imgur.com/6Ui0R4t.gif)

## Introduction

Shellmounter is a script for easy mounting removable disks in shell.

Features:

* Easy selection of filesystem
  * Completion for `mount` `unmount` and `toggle` command
  * Details in completion menu: partition label, size, device model
  * Batch operation: select a device to mount or unmount all filesystems inside
* Mount: smart directory switching
  * One filesystem is mounted: switch to the mount point
  * Multiple filesystems are mounted: switch to common prefix of the mount points
* Unmount: smart filesystem occupation detection
  * Automatically switch away, when current shell occupies the filesystem
  * Automatically show processes occupying the filesystem when unmount fails

## Install
### oh-my-zsh

First download shellmounter:

```zsh
cd ~/.oh-my-zsh/custom/plugins
git clone https://github.com/hghwng/shellmounter
```

Then enable the plugin in `~/.zshrc`

```zsh
plugins=(... shellmounter)
```

### Prezto
First download shellmounter:

```zsh
cd ~/.zprezto/modules
git clone https://github.com/hghwng/shellmounter
```

Then enable the plugin in `~/.zpreztorc`

```zsh
zstyle ':prezto:load' pmodule \
   [...] \
  'shellmounter'
```

## Using shellmounter
Shellmounter enables some aliases by default:

```zsh
alias um='shellmounter mount'
alias uu='shellmounter unmount'
alias ut='shellmounter toggle'
alias us='shellmounter status'
```

### Basic usage
```zsh
# Check mount status, '*' stands for already mounted.
~ % us
  sdb2  backup(215G)
  sdb1  general(785G)
  sdc4  CENTOS(8G)

# Mount all by toggle mount status
~ % ut
Info: mounting sdc4 sdb1 sdb2
Info: multiple directories mounted:
        /run/media/hugh/CENTOS
        /run/media/hugh/general
        /run/media/hugh/backup

# Unmount all by toggle mount status
~ % ut
```

### Specify devices to operate on
For `mount` `unmount` and `toggle`, you can specify filesystems to operate on by label, block device path and mountpoint:

```zsh
~ % um ARCH_201410              # mount by lable
~ % um /dev/sdb1                # mount by block device
~ % uu /run/media/hugh/dummy    # unmount filesystem mounted at /run/media/hugh/dummy
```

You can also operate on multiple filesystems:

```zsh
~ % um                          # mount all
~ % uu LabelOne LabelTwo
~ % um /dev/sdb                 # mount /dev/sdb1 /dev/sdb2, etc
~ % uu /dev/sdb LabelOne        # Mix block device and label
```

### Toggle state of devices
If there are filesystems not mounted yet, calling `toggle` without parameters will mount them. If every filesystems are mounted, calling `toggle` without parameters will unmount every filesystem.

Calling `toggle` with parameters requires that all filesystems selected should be in the same state, i.e. all mounted or all unmounted. Then the command will switch the state between mounted and unmounted.
