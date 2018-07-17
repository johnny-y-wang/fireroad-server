# FireRoad Server

FireRoad is an iOS (and hopefully soon, web) application providing MIT students with accessible information about courses, subjects, and schedules. The FireRoad Server is a Django server that currently provides simple catalog auto-updating services but is intended to expand into course suggestion features later on.

The `master` branch of this repo is intended to be checked out and run by the production server. All changes not ready for `master` should be kept in the `develop` branch.

## Setup

Once you have checked out the repo, you will need to generate a secret key, for example:

```
$ cd fireroad
$ openssl rand -base64 80 > fireroad/secret.txt
```

You will then need to create a file called `dbcreds.py` within the (inner) `fireroad` directory that defines the following variables: `dbname`, `username`, `password`, and `host`. These are used to initialize the MySQL database in `settings.py`.

Finally, you will need a file at `recommend/oidc.txt` that contains two lines: one with the client ID and one with the client secret for the OAuth authorization server.