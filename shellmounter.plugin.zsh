ZSH_SHELLMOUNTER_SCRIPT=${0:a:h}/shellmounter.py

function shellmounter() {
	cmd="$($ZSH_SHELLMOUNTER_SCRIPT $@)"
	eval "$cmd"
}

alias um='shellmounter mount'
alias uu='shellmounter unmount'
alias ut='shellmounter toggle'
alias us='shellmounter status'
