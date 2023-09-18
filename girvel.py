import cli


if __name__ == '__main__':
    args = cli.parser.parse_args()
    args.func(args)
