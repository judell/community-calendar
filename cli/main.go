package main

import (
	"fmt"
	"os"

	"github.com/judell/community-calendar/cli/cmd"
)

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(1)
	}

	var err error
	switch os.Args[1] {
	case "init":
		err = cmd.Init()
	case "build":
		err = cmd.Build()
	case "status":
		err = cmd.Status()
	case "version":
		fmt.Println("cc-cli v0.1.4")
	case "help", "--help", "-h":
		printUsage()
	default:
		fmt.Fprintf(os.Stderr, "Unknown command: %s\n", os.Args[1])
		printUsage()
		os.Exit(1)
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

func printUsage() {
	fmt.Println(`cc-cli - Community Calendar CLI

Usage:
  cc-cli <command>

Commands:
  init      Set up a new fork with its own Supabase backend
  build     Trigger the generate-calendar workflow
  status    Show recent workflow runs
  version   Print version
  help      Show this help`)
}
