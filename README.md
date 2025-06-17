### Test Application

Let\'s try Description here

## Features

### Tunisia Chart of Accounts (COA) - Automatic Configuration

This app includes an automatic configuration tool for Tunisian companies with the proper Chart of Accounts. When installed, it will:

- Automatically import the complete Tunisia Chart of Accounts for all existing companies
- Automatically configure all Tunisia-specific accounts for each company
- Set up Tax Templates for all Tunisia VAT rates (19%, 13%, 7%, 0%)
- Configure payment methods with proper account linkages
- Set up warehouse account connections for proper inventory accounting

The configuration runs automatically:
1. For all existing companies when the app is installed
2. For any new company when it's created

No manual action is required - everything is configured automatically!

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app my_custom_app
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/my_custom_app
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
