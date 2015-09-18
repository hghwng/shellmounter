ZSH_SHELLMOUNTER_SCRIPT=${0:a:h}/shellmounter.py

local -a precwd
function shellmounter() {
	# to prevent current shell's occupying the device, cd to / first
	# PWD will be read and written by python script
	builtin cd /

	cmd="$($ZSH_SHELLMOUNTER_SCRIPT $@)"
	eval "$cmd"

	builtin cd "$PWD"
}

alias um='shellmounter mount'
alias uu='shellmounter unmount'
alias ut='shellmounter toggle'
alias us='shellmounter status'
