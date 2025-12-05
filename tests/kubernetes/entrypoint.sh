#!/bin/bash
# SPDX-FileCopyrightText: 2014-2025 The VILLASframework Authors
# SPDX-License-Identifier: Apache-2.0

sleep_interruptible() {
	REM=$1

	while (( ${REM} > 0 )); do
		sleep 1
		REM=$((${REM} - 1))
		echo "Remaining: ${REM}"
	done
}

trap_with_arg() {
	func="$1" ; shift
	for sig ; do
		trap "$func $sig" "$sig"
	done
}

trap_handler() {
	echo "Received signal $1"

	if [[ $1 == "TERM" ]]; then
		echo "Now terminating.."
		exit
	fi
}

trap_with_arg trap_handler INT TERM CONT EXIT

RUNTIME=${RUNTIME:-120}

echo "My PID is $$"
echo "Starting workload for ${RUNTIME} seconds"

sleep_interruptible ${RUNTIME}
