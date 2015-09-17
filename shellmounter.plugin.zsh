ZSH_USBMOUNT_SCRIPT=${0:a:h}/usbmount.py

function usbmount() {
	cmd="$($ZSH_USBMOUNT_SCRIPT $@)"
	eval "$cmd"
}

alias um='usbmount mount'
alias uu='usbmount unmount'
alias ut='usbmount toggle'
alias us='usbmount status'
