---
name: Bug report
about: Create an issue  when you think you've found a bug in the Solcast integration
title: ''
labels: ''
assignees: ''

---
### Help us help you.

#### Do not create issues for questions on how to use or set up this integration - use the discussions for general support.  Only create issues to report geniune suspected bugs in the integration.

##### This issue template requests debug logs.  Please provide them.  Please don't provide screenshots of logs, or say "_logs look clean_" or assume they're not needed.  This integration works extremely well except when it fails, and when it fails, unless debug logs are provided, our chances of working out why it has failed are close to zero.

Note the instructions for getting debug logs, and follow them.

#### Fill in **all** of the data requested.

By failing to provide debug logs, you're providing us with permission to ignore you, or, at best, say **_debug logs required_**, and then ignore you.  By being lazy and not bothering to fill in data, you're encouraging us to be lazy and not bother responding.

By complaining that we're not treating you kindly or welcoming you, you're encouraging us to block you from this repo.  Please don't encourage us to block you; it's far quicker and easier for us to block you than to ~~argue~~ _discuss github etiquette_ with you, and we'll opt for quick and easy almost every time.

Feel free to delete everything above this line.

---

## Describe the bug

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behaviour:

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected behaviour

A clear and concise description of what you expected to happen.

## Screenshots

If applicable, add screenshots to help explain your problem.

## Logs

I confirm:

- [ ] I have attached **debug** logs
- [ ] I have embedded **debug** logs in the issue description (enclosed in tick marks ``` for proper formatting)
- [ ] Confirmed **debug** logs are not required for this issue

Make sure you include logs from HA listing the output from the Solcast integration showing the error - this is particularly useful in debugging issues and helping to determine whether the issue is with the integration or the Solcast service

To add detailed debug information, add the following to your configuration.yaml and restart HA:

``` yaml
logger:
  default: warn
  logs:
    custom_components.solcast_solar: debug
```

To inspect and collect debug logs examine `/config/home-assistant.log` using File Editor or Visual Studio Code Server.

If you are using docker, it sometimes can be easier to gather logs using `docker compose logs -n 500 -f homeassistant` or similar

## Solcast Integration Version

- Integration Version [e.g. 4.0.29]

## Desktop (please complete the following information)

- OS: [e.g. iOS]
- Browser [e.g. chrome, safari]
- Version [e.g. 22]

## Smartphone (please complete the following information)

- Device: [e.g. iPhone6]
- OS: [e.g. iOS8.1]
- Browser [e.g. stock browser, safari]
- Version [e.g. 22]

## Additional context

Add any other context about the problem here.
