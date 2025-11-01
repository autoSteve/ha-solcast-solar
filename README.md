# HA Solcast PV Solar Forecast Integration

<!--[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)-->
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
![GitHub Release](https://img.shields.io/github/v/release/BJReplay/ha-solcast-solar?style=for-the-badge)
[![hacs_downloads](https://img.shields.io/github/downloads/BJReplay/ha-solcast-solar/latest/total?style=for-the-badge)](https://github.com/BJReplay/ha-solcast-solar/releases/latest)
![GitHub License](https://img.shields.io/github/license/BJReplay/ha-solcast-solar?style=for-the-badge)
![GitHub commit activity](https://img.shields.io/github/commit-activity/y/BJReplay/ha-solcast-solar?style=for-the-badge)
![Maintenance](https://img.shields.io/maintenance/yes/2025?style=for-the-badge)

## Preamble

This custom component integrates the Solcast PV Forecast for hobbyists into Home Assistant (https://www.home-assistant.io).

It allows visualisation of the solar forecast in the Energy dashboard, and supports flexible forecast dampening, the application of a hard limit for over-sized PV systems, a comprehensive set of sensor and configuration entities, along with sensor attributes containing full forecast detail to support automation and visualisation.

It is a mature integration with an active community, and responsive developers.

This integration is not created by, maintained, endorsed nor approved by Solcast.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/solar_production.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/solar_production.png)

> [!NOTE]
>
> 
> This integration can be used as a replacement for the aging oziee/ha-solcast-solar integration, which is no longer being developed and has been removed. Uninstalling the Oziee version then installing this one, or simply downloading this one over that one will preserve all history and configuration. If you **uninstalled** the Oziee integration, and then installed this one, then you will need to re-select to use Solcast Solar as the source of forecast production for your Energy dashboard.

# Table of contents
1. [Key Solcast integration concepts](#key-solcast-integration-concepts)
1. [Solcast requirements](#solcast-requirements)
1. [Installation](#installation)
    1. [HACS recommended](#hacs-recommended)
    1. [Installing manually in HACS](#installing-manually-in-hacs)
    1. [Installing manually (not using HACS)](#installing-manually-(not-using-hacs))
    1. [Beta versions](#beta-versions)
1. [Configuration](#configuration)
    1. [Updating forecasts](#updating-forecasts)
        1. [Auto-update of forecasts](#auto-update-of-forecasts)
        1. [Using an HA automation to update forecasts](#using-an-ha-automation-to-update-forecasts)
    1. [Set up HA energy dashboard settings](#set-up-ha-energy-dashboard-settings)
1. [Interacting](#interacting)
    1. [Sensors](#sensors)
    1. [Attributes](#attributes)
    1. [Actions](#actions)
    1. [Configuration](#configuration)
    1. [Diagnostic](#diagnostic)
1. [Advanced configuration](#advanced-configuration)
    1. [Dampening configuration](#dampening-configuration)
        1. [Automated dampening](#automated-dampening)
        1. [Simple hourly dampening](#simple-hourly-dampening)
        1. [Granular dampening](#granular-dampening)
        1. [Reading forecast values in an automation](#reading-forecast-values-in-an-automation)
        1. [Reading dampening values](#reading-dampening-values)
    1. [Sensor attributes configuration](#sensor-attributes-configuration)
    1. [Hard limit configuration](#hard-limit-configuration)
    1. [Excluded sites configuration](#excluded-sites-configuration)
    1. [Advanced configuration options](#advanced-configuration-options)
1. [Sample template sensors](#sample-template-sensors)
1. [Sample Apex chart for dashboard](#sample-apex-chart-for-dashboard)
1. [Known issues](#known-issues)
1. [Troubleshooting](#troubleshooting)
1. [Complete integration removal](#complete-integration-removal)
1. [Changes](#Changes)

## Key Solcast integration concepts

The Solcast service produces a forecast of solar PV generation from today through to the end of up to thirteen days into the future. This is a total of up to fourteen days. The first seven of these day forecasts are exposed by the integration as a separate sensor, with the value being the total predicted solar generation for each day. Further forecasted days are not exposed by sensors, yet can be visualised on the Energy dashboard.

Separate sensors are also available that contain the expected peak generation power, peak generation time, and various forecasts of next hour, 30 minutes, and more.

If multiple arrays exist on different roof orientations, these can be configured in your Solcast account as separate 'rooftop sites' with differing azimuth, tilt and peak generation, to a maximum of two sites for a free hobbyist account. These separate site forecasts are combined to form the integration sensor values and Energy dashboard forecast data.

Three solar generation estimates are produced by Solcast for every half hour period of all forecasted days.

* 'central' or 50% or most likely to occur forecast is exposed as the `estimate` by the integration.
* '10%' or 1 in 10 'worst case' forecast assuming more cloud coverage than expected, exposed as `estimate10`.
* '90%' or 1 in 10 'best case' forecast assuming less cloud coverage than expected, exposed as `estimate90`.

The detail of these different forecast estimates can be found in sensor attributes, which contain both 30-minute daily intervals, and calculated hourly intervals across the day. Separate attributes sum the available estimates or break things down by Solcast site. (This integration usually references a Solcast site by by its 'site resource ID', and this can be found at the Solcast site https://toolkit.solcast.com.au/)

The Energy dashboard in Home Assistant is populated with historical data that is provided by the integration, with data retained for up to two years. (Forecast history is not stored as Home Assistant statistics, rather is stored in a `json` cache file maintained by the integration.) History displayed can be past forecasts, or "estimated actual" data, selectable as a configuration option.

Manipulation of forecasted values to account for predicable shading at times of the day is possible automatically, or by setting dampening factors for hourly or half-hourly periods. A "hard limit" may also be set for over-sized solar arrays where expected generation cannot exceed an inverter maximum rating. These two mechanisms are the only ways to manipulate the Solcast forecast data.

Solcast also produce historical estimated actual data. This is generally more accurate than a forecast because high resolution satellite imagery, weather and other climate observations (like water vapour and smog) are used to calculate the estimates. The integration automated dampening feature can make use of estimated actual data and compare it to generation history to provide a model of reduced forecasted generation to account for local shading. Estimated actual data can also be visualised on the Energy dashboard, whether automated dampening is used or not.

> [!NOTE]
>
> 
> Solcast have altered their API limits. New hobbyist account creators are allowed a maximum of 10 API calls per day. Original hobbyist users will retain up to 50 calls per day.

## Solcast requirements

Sign up for an API key (https://solcast.com/).

> Solcast may take up to 24hrs to create the account.

Configure your rooftop sites correctly at `solcast.com`.

Remove any sample sites from your Solcast dashboard (see [Known issues](#known-issues) for examples of sample sites and the issue that might occur if you don't remove them.)

Copy the API key for use with this integration (See [Configuration](#Configuration) below).

Note the importance of getting your Solcast site configuration correct. Use the "Site is facing" hint to ensure the azimuth is signed correctly, as if this is incorrect then forecasts will appear shifted, possibly by up to an hour during the day.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/azimuth_tilt.png" width="600">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/azimuth_tilt.png)

Azimuth is _not_ set as a 0-359 degree value, but rather as 0-180 for westerly facing, or zero to _minus_ 179 for easterly facing. This value is the number of degrees angled away from North, with the sign being West or East. If you're not sure, then do some quick research.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/azimuth.png" width="300">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/azimuth.png)

An old-school method that can work is to get a North-oriented Google Maps satellite image of your home and measure azimuth using a plastic 180 degree protractor with its straight edge aligned North/South on screen and its centre point on the side of a representative panel. Count the degrees away from North. For westerly or easterly flip the protractor. You may need to screen grab the Maps image into a PNG/JPG and add line extensions to the orientation to be able to accurately measure the angle.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/azimuth_house.png" width="300">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/azimuth_house.png)

Using Google Earth or ChatGPT are other alternatives.

> [!NOTE]
>
>
> Solcast are headquartered in Sydney, Australia in the southern hemisphere, and use azimuth numbering as degrees pointed away from North. If you live in the northern hemisphere then it is likely that any online mapping service that can be used to determine azimuth will use a numbering convention that is degrees pointed away from _South_, which will yield incompatible values.
>
> A Solcast configuration of roof aligned North/North-East/North-West in the northern hemisphere or South/South-East/South-West in the southern hemisphere is considered to be possibly unusual because these orientations are not directly facing the sun at any time.
>
> On start-up, the integration will validate your Solcast azimuth setting in order to highlight a potential misconfiguration and will issue a warning message in the Home Assistant log and raise an issue if it detects an unusual roof alignment. If you receive this warning and have confirmed your Solcast settings are correct then the warning message can simply be ignored. The warning is there to try to catch configuration mistakes.
>
> There are always outlier installations, like two rooftops that face both West and East with panels installed on both faces, 180 degrees from each other. One rooftop is going to be considered "unusual". Check the azimuth according to Solcast, and fix or ignore the warning as appropriate. Remember, 0° = NORTH according to Solcast, with orientations being relative to this.

## Installation

### HACS recommended

*(Recommended installation method)*

Install as a Default Repository using HACS. More info about HACS can be found [here](https://hacs.xyz/).  If you haven't installed HACS yet, go do it first!

The easiest way to install the integration is to click the button below to open this page in your Home Assistant HACS page (you will be prompted for your Home Assistant URL if you've never used this type of button before).

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=BJReplay&repository=ha-solcast-solar&category=integration)

You'll be prompted to confirm you want to open the repository inside HACS inside Home Assistant:

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/OpenPageinyourHomeAssistant.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/OpenPageinyourHomeAssistant.png)

You'll see this page, with a `↓ Download` button near the bottom right - click on it:

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/Download.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/Download.png)

You'll be prompted to download the Solcast PV Forecast component - click on `Download`:

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SolcastPVSolar.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SolcastPVSolar.png)

Once it is installed, you'll probably notice a notification pop up on `Settings`:

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SettingsNotification.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SettingsNotification.png)

Click on settings, and you should see a Repair notification for `Restart required`:

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/RestartRequired.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/RestartRequired.png)

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/RestartSubmit.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/RestartSubmit.png)

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SuccessIssueRepaired.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SuccessIssueRepaired.png)

If you don't see this (you might be running an older version of Home Assistant), navigate to `System`, `Settings`, click on the power Icon, and `Restart Home Assistant`.  You need to restart Home Assistant before you can then configure the Solcast PV Forecast custom component that you've just downloaded.

Once you've restarted, follow along at [Configuration](#configuration) to continue setting up the Solcast PV Forecast integration component.

### Installing manually in HACS

More info [here](https://hacs.xyz/docs/faq/custom_repositories/)

1. (If using it, remove oziee/ha-solcast-solar in HACS)
1. Add custom repository (three vertical dots menu, top right) `https://github.com/BJReplay/ha-solcast-solar` as an `integration`
1. Search for 'Solcast' in HACS, open it and click the `Download` button
1. See [Configuration](#configuration) below

If previously using Oziee's ha-solcast-solar then all history and config should remain.

### Installing manually (not using HACS)

You probably **do not** want to do this! Use the HACS method above unless you know what you are doing and have a good reason as to why you are installing manually.

1. Using the tool of choice open the folder (directory) for your HA configuration (where you find `configuration.yaml`)
1. If you do not have a `custom_components` folder there, you need to create it
1. In the `custom_components` folder create a new folder called `solcast_solar`
1. Download _all_ the files from the `custom_components/solcast_solar/` folder in this repository
1. Place the files you downloaded in the new folder you created
1. *Restart HA to load the new integration*
1. See [Configuration](#configuration) below

### Beta versions

Beta versions may be available that fix issues.

Check https://github.com/BJReplay/ha-solcast-solar/releases to see if an issue has already been resolved. If so, enable the `Solcast PV Pre-release` entity to enable beta upgrade (or for HACS v1 turn on `Show beta versions` when re-downloading).

Your feedback from testing betas is most welcome in the repository discussions at https://github.com/BJReplay/ha-solcast-solar/discussions, where a discussion will exist for any active beta.

## Configuration

1. [Click Here](https://my.home-assistant.io/redirect/config_flow_start/?domain=solcast_solar) to directly add a `Solcast Solar` integration **or**<br/>
 a. In Home Assistant, go to Settings -> [Integrations](https://my.home-assistant.io/redirect/integrations/)<br/>
 b. Click `+ Add Integrations`

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/AddIntegration.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/AddIntegration.png)

 and start typing `Solcast PV Forecast` to bring up the Solcast PV Forecast integration, and select it.<br/>
 
 [<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/Setupanewintegration.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/Setupanewintegration.png)

1. Enter your `Solcast API Key`, `API limit`, desired auto-update choice and click `Submit`. If you have more than one Solcast account because you have more than two rooftop setups, enter all Solcast account API keys separated by a comma `xxxxxxxx-xxxxx-xxxx,yyyyyyyy-yyyyy-yyyy`. (_Note: This may breach Solcast terms and conditions by having more than one account if the locations of these account sites are within one kilometre of each other, or 0.62 miles._) Your API limit will be 10 for new Solcast users or 50 for early adopters. If the API limit is the same for multiple accounts then enter a single value for that, or both values separated by a comma, or the least API limit of all accounts as a single value. See [Excluded sites configuration](#excluded-sites-configuration) for a multiple API key use case.
1. If an auto-update option was not chosen then create your own automation to call the action `solcast_solar.update_forecasts` at the times you would like to update the solar forecast.
1. Set up the Home Assistant Energy dashboard settings.
1. To change other configuration options after installation, select the integration in `Devices & Services` then `CONFIGURE`.

Make sure you use your `API Key` and not your rooftop ID created in Solcast. You can find your API key here [api key](https://toolkit.solcast.com.au/account).

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/install.png" width="500">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/install.png)

> [!IMPORTANT]
> The API key and associated sites will be checked when the initial configuration is saved. It is possible for this initial check to fail because the Solcast API is temporarily unavailable, and if it is then simply retry configuration after some minutes. The configure error message will indicate if this is the case.

### Updating forecasts

#### Auto-update of forecasts

The default for new installations is automatic scheduled forecast update.

Using auto-update will get forecast updates that are automatically spread across hours when the sun is up, or alternatively over a 24-hour period. It calculates the number of daily updates that will occur according to the number of Solcast sites and the API limit that is configured (or lowest limit in the case of multiple API keys).

Should it be desired to fetch an update outside of these hours, then the API limit in the integration configuration may be reduced, and an automation may then be set up to call the action `solcast_solar.force_update_forecasts` at the desired time of day. (Note that calling the action `solcast_solar.update_forecasts` will be refused if auto-update is enabled, so use force update instead.)

For example, to update just after midnight, as well as take advantage of auto-update, create the desired automation to force update, then reduce the API limit configured in the automation accordingly. (For this example, if the API key has ten total calls allowed per day and two rooftop sites, reduce the API limit to eight because two updates will be used when the automation runs.)

Using force update will not increment the API use counter, which is by design.

> [!NOTE]
> _Transitioning to auto-update from using an automation:_
>
> If currently using the recommended automation, which spreads updates fairly evenly between sunrise and sunset, turning on auto-update from sunrise to sunset should not cause unexpected forecast fetch failures due to API limit exhaustion. The recommended automation is not identical to auto-update but is fairly close in timing.
>
> If implementing a reduced API limit, plus a further forced update at a different time of day (like midnight), then a 24-hour period of adjustment may be needed, which could possibly see API exhaustion reported even if the Solcast API usage count has not actually been exhausted. These errors will clear within 24 hours.

#### Using an HA automation to update forecasts

If auto-update is not enabled then create a new automation (or automations) and set up your preferred trigger times to poll for new Solcast forecast data. Use the action `solcast_solar.update_forecasts`. Examples are provided, so alter these or create your own to fit your needs.

<details><summary><i>Click here for the examples</i><p/></summary>

To make the most of the available API calls per day, you can have the automation call the API using an interval calculated by the number of daytime hours divided by the number of total API calls a day you can make.

This automation bases execution times on sunrise and sunset, which differ around the globe, so inherently spreads the load on Solcast. It is very similar to the behaviour of auto-update from sunrise to sunset, with the difference being that it also incorporates a randomised time offset, which will hopefully further avoid the likelihood that the Solcast servers get inundated by multiple callers at the same time.

```yaml
alias: Solcast update
description: ""
triggers:
  - trigger: template
    value_template: >-
      {% set nr = as_datetime(state_attr('sun.sun','next_rising')) | as_local %}
      {% set ns = as_datetime(state_attr('sun.sun','next_setting')) | as_local %}
      {% set api_request_limit = 10 %}
      {% if nr > ns %}
        {% set nr = nr - timedelta(hours = 24) %} 
      {% endif %}
      {% set hours_difference = (ns - nr) %}
      {% set interval_hours = hours_difference / api_request_limit %}
      {% set ns = namespace(match = false) %}
      {% for i in range(api_request_limit) %}
        {% set start_time = nr + (i * interval_hours) %}
        {% if ((start_time - timedelta(seconds=30)) <= now()) and (now() <= (start_time + timedelta(seconds=30))) %}
          {% set ns.match = true %}
        {% endif %}
      {% endfor %}
      {{ ns.match }}
conditions:
  - condition: sun
    before: sunset
    after: sunrise
actions:
  - delay:
      seconds: "{{ range(30, 360)|random|int }}"
  - action: solcast_solar.update_forecasts
    data: {}
mode: single
```

> [!NOTE]
>
> 
> If you have two arrays on your roof then two API calls will be made for each update, effectively reducing the number of updates to five per day. For this case, change to: `api_request_limit = 5`

The next automation also includes a randomisation so that calls aren't made at precisely the same time, hopefully avoiding the likelihood that the Solcast servers are inundated by multiple calls at the same time, but it triggers every four hours between sunrise and sunset:

```yaml
alias: Solcast_update
description: New API call Solcast
triggers:
 - trigger: time_pattern
   hours: /4
conditions:
 - condition: sun
   before: sunset
   after: sunrise
actions:
 - delay:
     seconds: "{{ range(30, 360)|random|int }}"
 - action: solcast_solar.update_forecasts
   data: {}
mode: single
```

The next automation triggers at 4am, 10am and 4pm, with a random delay.

```yaml
alias: Solcast update
description: ""
triggers:
  - trigger: time
    at:
      - "4:00:00"
      - "10:00:00"
      - "16:00:00"
conditions: []
actions:
  - delay:
      seconds: "{{ range(30, 360)|random|int }}"
  - action: solcast_solar.update_forecasts
    data: {}
mode: single
```
</details>

> [!TIP]
>
> 
> The Solcast Servers seem to occasionally be under some strain, and the servers return 429/Too busy return codes at these times. The integration will automatically pause, then retry the connection several times, but occasionally even this strategy can fail to download forecast data.
>
> Changing your API Key is not a solution, nor is uninstalling and re-installing the integration. These "tricks" might appear to work, but all that has actually happened is that you have tried again later, and the integration has worked as the Solcast servers are less busy.
> 
> To find out whether this is your issue look at the Home Assistant logs. To get detailed information (which is required when raising an issue) make sure that you have debug logging turned on.
>
> Log capture instructions are in the Bug Issue Template - you will see them if you start creating a new issue - make sure you include these logs if you want the assistance of the repository contributors.
>
> An example of busy messages and a successful retry are shown below (with debug logging enabled). In this case there is no issue, as the retry succeeds. Should ten consecutive attempts fail, then the forecast retrieval will end with an `ERROR`. If that happens, manually trigger another `solcast_solar.update_forecasts` action (or if auto-update is enabled use `solcast_solar.force_update_forecasts`), or wait for the next scheduled update.
>
> Should the load of sites data on integration startup be the call that has failed with 429/Too busy, then the integration will start if sites have been previously cached and it will blindly use this cached information. If changes to sites have been made then these changes will not be read in this circumstance, and unexpected results may occur. If things are unexpected then check the log. Always check the log if things are unexpected, and a restart will likely read the updated sites correctly.

```
INFO (MainThread) [custom_components.solcast_solar.solcastapi] Getting forecast update for site 1234-5678-9012-3456
DEBUG (MainThread) [custom_components.solcast_solar.solcastapi] Polling API for site 1234-5678-9012-3456
DEBUG (MainThread) [custom_components.solcast_solar.solcastapi] Fetch data url - https://api.solcast.com.au/rooftop_sites/1234-5678-9012-3456/forecasts
DEBUG (MainThread) [custom_components.solcast_solar.solcastapi] Fetching forecast
WARNING (MainThread) [custom_components.solcast_solar.solcastapi] Solcast API is busy, pausing 55 seconds before retry
DEBUG (MainThread) [custom_components.solcast_solar.solcastapi] Fetching forecast
DEBUG (MainThread) [custom_components.solcast_solar.solcastapi] API returned data. API Counter incremented from 35 to 36
DEBUG (MainThread) [custom_components.solcast_solar.solcastapi] Writing usage cache
DEBUG (MainThread) [custom_components.solcast_solar.solcastapi] HTTP session returned data type <class 'dict'>
DEBUG (MainThread) [custom_components.solcast_solar.solcastapi] HTTP session status is 200/Success
```

### Set up HA energy dashboard settings

Go to `Settings`, `Dashboards`, `Energy`

The solar forecast has to be associated with a solar generation item in your Energy dashboard.

Edit a `Solar Panels` `Solar production` item you have previously created (or will create now). Do not add a separate `Solar production` item as things will just get weird.

There can only be a single configuration of the total Solcast PV Forecast in the Energy dashboard, it is not possible to split the forecast for different solar arrays/Solcast sites.

> [!IMPORTANT]  
> If you do not have a solar generation sensor in your system then this integration will not work in the Energy dashboard. The graph and adding the forecast integration rely on there being a generation sensor set up.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SolarPanels.png" width="500">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SolarPanels.png)

Select `Forecast Production` and select the `Solcast Solar` option. Click `SAVE`, and Home Assistant will do the rest for you.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SolcastSolar.png" width="500">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SolcastSolar.png)

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/solar_production.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/solar_production.png)

## Interacting

There are many actions, sensors and configuration items exposed by the integration, along with many sensor attributes that may be enabled.

Utilise the Home Assistant `Developer tools` to examine exposed attributes, as their naming is mostly deployment specific. Refer to examples elsewhere in this readme to gain an insight as to how they may be used.

There is also a collection of Jinja2 templates provided at https://github.com/BJReplay/ha-solcast-solar/blob/main/TEMPLATES.md containing basic, intermediate and advanced templating examples.

### Sensors

All sensor names are preceded by the integration name `Solcast PV Forecast`.

| Name | Type | Attributes | Unit | Description |
| ------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `Forecast Today` | number | Y | `kWh` | Total forecast solar production for today. |
| `Forecast Tomorrow` | number | Y | `kWh` | Total forecast solar production for day + 1 (tomorrow). |
| `Forecast Day 3` | number | Y | `kWh` | Total forecast solar production for day + 2 (day 3, disabled by default). |
| `Forecast Day 4` | number | Y | `kWh` | Total forecast solar production for day + 3 (day 4, disabled by default). |
| `Forecast Day 5` | number | Y | `kWh` | Total forecast solar production for day + 4 (day 5, disabled by default). |
| `Forecast Day 6` | number | Y | `kWh`| Total forecast solar production for day + 5 (day 6, disabled by default). |
| `Forecast Day 7` | number | Y | `kWh` | Total forecast solar production for day + 6 (day 7, disabled by default). |
| `Forecast This Hour` | number | Y | `Wh` | Forecasted solar production current hour (attributes contain site breakdown). |
| `Forecast Next Hour` | number | Y | `Wh` | Forecasted solar production next hour (attributes contain site breakdown). |
| `Forecast Next X Hours` | number | Y | `Wh` | Custom user defined forecasted solar production for next X hours, disabled by default<br>Note: This forecast starts at current time, it is not aligned on the hour like "This hour", "Next Hour". |
| `Forecast Remaining Today` | number | Y | `kWh` | Predicted remaining solar production today. |
| `Peak Forecast Today` | number | Y | `W` | Highest predicted production within an hour period today (attributes contain site breakdown). |
| `Peak Time Today` | date/time | Y |  | Hour of max forecasted production of solar today (attributes contain site breakdown). |
| `Peak Forecast Tomorrow` | number | Y | `W` | Highest predicted production within an hour period tomorrow (attributes contain site breakdown). |
| `Peak Time Tomorrow` | date/time | Y |  | Hour of max forecasted production of solar tomorrow (attributes contain site breakdown). |
| `Forecast Power Now` | number | Y | `W` | Predicted nominal solar power this moment (attributes contain site breakdown). |
| `Forecast Power in 30 Minutes` | number | Y | `W` | Predicted nominal solar power in 30 minutes (attributes contain site breakdown). |
| `Forecast Power in 1 Hour` | number | Y | `W` | Predicted nominal solar power in 1 hour (attributes contain site breakdown). |

> [!NOTE]
>
> 
> Where a site breakdown is available as an attribute, the attribute name is the Solcast site resource ID (with hyphens replaced by underscores).
>
> 
> Most sensors also include an attribute for `estimate`, `estimate10` and `estimate90`. Template sensors may be created to expose their value, or the `state_attr()` can be used directly in automations.
>
> 
> Access these in a template sensor or automation using something like:
>
> 
> ```
> {{ state_attr('sensor.solcast_pv_forecast_peak_forecast_today', '1234_5678_9012_3456') | float(0) }}
> {{ state_attr('sensor.solcast_pv_forecast_peak_forecast_today', 'estimate10') | float(0) }}
> {{ state_attr('sensor.solcast_pv_forecast_peak_forecast_today', 'estimate10_1234_5678_9012_3456') | float(0) }}
> ```
>
> 
> Also see the sample PV graph below for how to chart forecast detail from the detailedForecast attribute.

> [!NOTE]
>
> 
> The values for `Next Hour` and `Forecast Next X Hours` may be different if the custom X hour setting is 1. This has a simple explanation.
>
> 
> They are calculated using a different start and end time. One is from the start of this hour, i.e. in the past, e.g. 14:00:00 to 15:00:00. The custom sensor is from "now" on five minute boundaries, e.g. 14:20:00 to 15:20:00 using interpolated values.
>
> 
> This will likely yield a different result, depending on the time the value is requested, so it is not wrong. It's just different.

### Attributes

As stated above, sensor attributes are created to enable sensor state variations to be used in templates. Examples are the estimate confidence, `estimate10`/`estimate`/`estimate90`. The sensor _state_ is generally left at the default of `estimate`, but displaying the tenth percentile of a sensor on a dashboard may be desired and this is enabled by the use of _attribute_ values.

Some attribute names are deployment specific (examples are given here), and some attributes are disabled by default or by user preference to clear clutter. These preferences are set in the `CONFIGURE` dialogue.

Attribute names must not contain a hyphen. Solcast site resource IDs _are_ named using a hyphen, so where an attribute is named for the site resource ID that it represents the hyphens are replaced with underscores.

All detailed forecast sensors that provide hourly or half-hourly breakdowns provide (as does the underlying Solcast data) data in kW - these are power sensors, not energy sensors, and represent the average power forecast for the period.

For all sensors:

* `estimate10`: 10th percentile forecast value (number)
* `estimate`: 50th percentile forecast value (number)
* `estimate90`: 90th percentile forecast value (number)
* `1234_5678_9012_3456`: An individual site value, i.e. a portion of the total (number)
* `estimate10_1234_5678_9012_3456`: 10th for an individual site value (number)
* `estimate_1234_5678_9012_3456`: 50th for an individual site value (number)
* `estimate90_1234_5678_9012_3456`: 90th for an individual site value (number)

For the `Forecast Next X Hours` sensor only:

* `custom_hours`: The number of hours reported by the sensor (number)

For daily forecast sensors only:

* `detailedForecast`: A half-hourly breakdown of expected average power generation for each interval (list of dicts, units in kW, not kWh), and if automated dampening is active then the factor determined for each interval is also included
* `detailedHourly`: An hourly breakdown of expected average power generation for each interval (list of dicts, units in kW)
* `detailedForecast_1234_5678_9012_3456`: A half-hourly site-specific breakdown of expected average power generation for each interval (list of dicts, units in kW)
* `detailedHourly_1234_5678_9012_3456`: An hourly site-specific breakdown of expected average power generation for each interval (list of dicts, units in kW)

The "list of dicts" has the following format, with example values used: (Note the inconsistency in `pv_estimateXX` vs. `estimateXX` used elsewhere. History is to blame.)

JSON:
```json
[
  {
    "period_start": "2025-04-06T08:00:00+10:00",
    "dampening_factor": 0.888, <== for detailedForecast only, and only if automated dampening is enabled
    "pv_estimate10": 10.000,
    "pv_estimate": 50.000,
    "pv_estimate90": 90.000
  },
  ...
]
```

YAML:
```yaml
- period_start: '2025-04-06T08:00:00+10:00'
  dampening_factor: 0.888, <== for detailedForecast only, and only if automated dampening is enabled
  pv_estimate10: 10.000
  pv_estimate: 50.000
  pv_estimate90: 90.000
- ...
```

### Actions

| Action | Description |
| --- | --- |
| `solcast_solar.update_forecasts` | Update the forecast data (refused if auto-update is enabled). |
| `solcast_solar.force_update_forecasts` | Force update the forecast data (performs an update regardless of API usage tracking or auto-update setting, and does not increment the API use counter, refused if auto-update is not enabled.) |
| `solcast_solar.force_update_estimates` | Force update the estimated actual data (does not increment the API use counter, refused if get estimated actuals is not enabled.) |
| `solcast_solar.clear_all_solcast_data` | Deletes cached data, and initiates an immediate fetch of new past actual and forecast values. |
| `solcast_solar.query_forecast_data` | Return a list of forecast data using a datetime range start - end. |
| `solcast_solar.query_estimate_data` | Return a list of estimated actual data using a datetime range start - end. |
| `solcast_solar.set_dampening` | Update the dampening factors. |
| `solcast_solar.get_dampening` | Get the currently set dampening factors. |
| `solcast_solar.set_hard_limit` | Set inverter forecast hard limit. |
| `solcast_solar.remove_hard_limit` | Remove inverter forecast hard limit. |

Example parameters are provided here for each `query`, `set` and `get` action. Use `Developer tools` | `Actions` to show the available parameters for each with a description. 

Where a 'site' parameter is needed, use the Solcast site resource ID and not the site name.

```yaml
action: solcast_solar.query_forecast_data
data:
  start_date_time: 2024-10-06T00:00:00.000Z
  end_date_time: 2024-10-06T10:00:00.000Z
  undampened: false (optional)
  site: 1234-5678-9012-3456 (optional)
```

```yaml
action: solcast_solar.query_estimate_data
data:
  start_date_time: 2024-10-06T00:00:00.000Z
  end_date_time: 2024-10-06T10:00:00.000Z
```

```yaml
action: solcast_solar.set_dampening
data:
  damp_factor: 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
  site: 1234-5678-9012-3456 (optional)
```

```yaml
action: solcast_solar.set_hard_limit
data:
  hard_limit: 6
```

```yaml
action: solcast_solar.get_dampening
data:
  site: 1234-5678-9012-3456 (optional)
```

### Configuration

| Name | Type | Description |
| ------------------------------ | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `Forecast Field` | selector | Select the forecast confidence used for sensor states as 'estimate', 'estimate10' or 'estimate90'. |

### Diagnostic

All diagnostic sensor names are preceded by `Solcast PV Forecast` except for `Rooftop site name`.

| Name | Type | Attributes | Unit | Description |
| ------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | 
| `API Last Polled` | date/time | Y | `datetime` | Date/time when the forecast was last updated successfully. |
| `API Limit` | number | N | `integer` | Total times the API can been called in a 24 hour period[^1]. |
| `API used` | number | N | `integer` | Total times the API has been called today (API counter resets to zero at midnight UTC)[^1]. |  
| `Dampening` | boolean | Y | `bool` | Whether dampening is enabled (disabled by default). |  
| `Hard Limit Set` | number | N | `float` or `bool` | `False` if not set, else value in `kilowatts`. |
| `Hard Limit Set ******AaBbCc` | number | N | `float` | Individual account hard limit. Value in `kilowatts`. |
| `Rooftop site name` | number | Y | `kWh` | Total forecast for rooftop today (attributes contain the site setup)[^2]. |

`API Last Polled` attributes include the following:

* `failure_count_today`: The count of failures (like `429/Too busy`) that have occurred since midnight local time.
* `failure_count_7_day`: The count of failures that have occurred over the past seven days.
* `last_attempt`: The date/time of last attempted forecast update. "Currently healthy" is considered last polled >= last attempt.

If auto-update is enabled then last polled also features these attributes:

* `auto_update_divisions`: The number of configured auto-updates for each day.
* `auto_update_queue`: A maximum of 48 future auto-updates currently in the queue.
* `next_auto_update`: The date/time of the next scheduled auto-update.

If dampening is active then the Dampening sensor also features these attributes:

* `integration_automated`: Boolean. Whether automated dampening is enabled.
* `last_updated`: Datetime. The date and time that the dampening factors were last set.
* `factors`: Dict. The `interval` start hour:minute, and `factor` as a floating point number.

Example dampening sensor attributes:

``` yaml
integration_automated: true
last_updated: 2025-08-26T04:03:01+00:00
factors: 
- interval: '00:00'
  factor: 1
- interval: '00:30'
  factor: 1
- interval: '01:00'
  factor: 1
...
```

`Rooftop site name` attributes include:

* `azimuth` / `tilt`: Panel orientation.
* `capacity`: Site capacity in AC power.
* `capacity_dc`: Site capacity in DC power.
* `install_date`: Configured installation date.
* `loss_factor`: Configured "loss factor".
* `name`: The site name configured at solcast.com.
* `resource_id`: The site resource ID.
* `tags`: The tags set for the rooftop site.

> [!NOTE]
>
> Latitude and longitude are intentionally not included in the rooftop site attributes for privacy reasons.

[^1]: API usage information is internally tracked and may not match actual account usage.

[^2]: Each rooftop created in Solcast will be listed separately.

## Advanced configuration

### Dampening configuration

Dampening values account for shading, and adjust forecasted generation. Dampening may be determined automatically, or determined outside of the integration and set with a service action.

Any change to dampening factors will be applied to future forecasts (including the forecast for the current day). Forecast history will retain the dampening that was in effect at the time.

Automated dampening (described below) will calculate overall "all rooftop sites" dampening factors. If per-rooftop site dampening is desired then it is possible to model that elsewhere with your own dampening solution and then set factors by using the `solcast_solar.set_dampening` action. See [Granular dampening](#granular-dampening) below.

> [!NOTE]
>
> When automated dampening is enabled it will not be possible to set dampening factors by service action, nor manually in the integration options, nor by writing the `solcast-dampening.json` file.
>
> (If the dampening file write method is attempted then the new file content will be ignored, and later overwritten with updated automated dampening factors when they are modelled.)


#### Automated dampening

A feature of the integration is automated dampening, where actual generation history is compared with estimated past generation to determine regularly anomalous generation. This is useful to identify periods of likely panel shading, and to then automatically apply a dampening factor for forecast periods during the day that are likely shade affected, reducing the forecasted energy accordingly.

Automated dampening is dynamic, and utilises up to fourteen 'rolling' days of generation and estimated generation data to build its model and determine dampening factors to apply. No more than fourteen days are used. At the time the feature is enabled any limit of history will possibly mean a reduced data set to utilise, but this will grow to fourteen days in time and improve modelling.

Automated dampening will apply the same dampening factors to all rooftop sites, based on total location generation and Solcast data.

> [!NOTE]
>
> Automated dampening may not work for you, especially because of the way that your generation entities report energy, or if you are on a wholesale energy market plan where prices can go negative so you limit site export at those times. (But do read on for a likely solution on that front.)
>
> This integrated automated dampening feature will suit many people, but it is not a panacea.
>
> It may look like a "tick and flick" option in the configuration, but this is not. It is a complex piece of code that has to deal with different types of PV generation reporting and possible communications issues between your inverter and Home Assistant, whilst spotting anomalous generation caused by shading.
>
> If you think automated dampening is not working correctly then please THINK, INVESTIGATE, and then REPORT any issues with automated dampening, in that order. Include details of why you think automated dampening is not working and the possible solution in any issue report.
>
> If you investigate and find that an issue is because of your hand-built generation entity then auto-dampening may not be for you and in this case please roll your own dampening solution, or be technically constructive in any suggested improvement. The component parts are available for you to build your own by utilising granular dampening.
>
> Do also check out the "advanced options" for the integration. There are many "nerd knobs" that may be set for automated dampening, and these may solve for your issue with it.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/automated-dampening.png" width="500">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/automated-dampening.png)

The theory of operation is simple, relying on two key inputs, and an optional third.

##### Theory of operation

Automated dampening first builds a "consistently best" set of (more than one) half-hourly [estimated actual](https://github.com/BJReplay/ha-solcast-solar/issues/373#key-input-estimated-actual-data-from-solcast) generation periods from the past fourteen days. (This is not actual site generation, but a "best guess" by Solcast of what should have been generated).

It then compares that to [generation history](#key-input-actual-pv-generation-for-your-site) for these periods (excluding generation periods where export limits may have been hit by [optional export limiting](#optional-input-site-export-to-the-grid-combined-with-a-limit-value), or when intentionally suppressed). The highest actual generation value is selected from the similar best-estimated actual periods, but only if there is more than one generation value. This value determines whether external factors are likely impacting generation, and is used to calculate a "base" dampening factor.

As automated dampening is looking to identify when shading is affecting your solar generation it will discard 'non-best estimated PV generation' day intervals. These are intervals on days when PV generation is reduced due to cloud, rain, etc.

Said another way, and in very simple English, Solcast have estimated in the past that production should have been 'X' kW average at a certain time on sunny days, but the most that has ever been achieved recently has been 'Y' kW, so the integration will adjust future forecasts towards 'Y'. Or even simpler, the estimated actual generation is consistently higher than what can be achieved, so reduce the forecast.

Because forecast periods vary from best estimates due to cloud cover, the base factor is then altered before it is applied to forecasts by using a logarithmic difference calculation. If the forecast solar generation varies significantly to the best estimated solar generation that was used to determine the base dampening factor, then it is adjusted so it has little impact (i.e. adjusted closer to a factor of 1.0). This determination is made based on the value of every forecasted interval, so each day will likely have different factors applied.

The base dampening factor adjustment is done because when there is significant forecasted generation variance for an interval compared to past better generation intervals it is indicative of a heavily clouded period being expected. This adapts dampening to suit cloudy periods, where diffuse light is the most significant component of solar generation and not direct sunlight, being the solar generation component most impacted by shade.

> [!TIP]
>
> Examine the `detailedForecast` attribute for each day forecast to see the automated dampening factors that have been applied to each interval. An Apex chart example is included in [`TEMPLATES.md`](https://github.com/BJReplay/ha-solcast-solar/blob/main/TEMPLATES.md) to show a practical application for this dampening information.

##### Key input: Estimated actual data from Solcast

Aside from forecasts, the Solcast service also estimates the likely past actual generation during the day for every rooftop site, based on high resolution satellite imagery, weather observations, and how "clear" the air is (vapour/smog). This data is referred to as an "estimated actual", and it is generally quite accurate for a given location.

Getting estimated actual data does require an API call, and that API call will use up API quota for a hobbyist user. You will need to factor API call consumption for this purpose when taking advantage of automated dampening, with one call used per configured Solcast rooftop site per day per API key. (Reduce the API limit for forecast updates in options by one for a single rooftop site, or by two for two sites.)

Past estimated actual data is acquired just after midnight each day local time, randomised to update within 15 minutes. Where automated dampening is enabled, new dampening factors for the day ahead are modelled immediately after the estimated actual update. It is also possible to force an update of the estimated actuals, and this will also attempt to model dampening factors if appropriate.

> [!TIP]
>
> If your aim is to obtain as many forecast updates during the day as possible, then using estimated actuals and automated dampening is not for you. It will reduce the number of forecast updates possible.

##### Key input: Actual PV generation for your site

Generation is gathered from history data of a sensor entity (or entities). A single PV solar inverter installation will likely have a single "total increasing" sensor that provides a "PV generation" or "PV export" value (_not_ export to grid, but export off your roof from the sun). Multiple inverters will have a value for each, and all sensor entities may be supplied, which will then be totalled for all rooftops.

An increasing energy sensor (or sensors) must be supplied. This increasing sensor may reset at midnight, or may be a "total increasing" type; of importance is that it is increasing throughout the day.

The integration determines the units by inspecting the `unit_of_measurement` attribute and adjusts accordingly. Where this attribute is not set it assumes values are kWh. Generation history updates occur at midnight local time.

> [!TIP]
>
> In order for the integration to be able to spot anomalous PV generation, it needs the generation entities to regularly report to Home Assistant. Entities that report a latest generation value periodically or increase in regular steps are supported. If your PV generation entity does not fall into a similar generation pattern then automated dampening might not work for you.

> [!NOTE]
>
> Do not include generation entities for "remote" rooftop sites that have been explicitly excluded from sensor totals. Auto-dampening does not work for excluded rooftops.

##### Optional input: Site export to the grid, combined with a limit value

Where locally generated excess power is exported to the electricity grid, it is likely that there will be a limit to the amount of energy that may be exported. The integration can monitor this export, and when periods of "export limiting" are detected (because export is at the limit value for five minutes or more) then the generation period will be excluded from any automated dampening consideration for _all_ days considered by automated dampening by default. This mechanism ensures differentiation of generation being limited by shade from a tree or chimney, or artificial site export limiting.

Export to the grid generally occurs in the middle of the day, which is a time rarely impacted by shading.

A single increasing energy sensor is allowed, and this may reset to zero at midnight. The optional export limit can only be specified in kW. See the advanced options section for ways to vary this "all days" excluded behaviour.

> [!TIP]
>
> An export limit value may not be precisely measured by some PV system components as the real limit. This may be confusing, but the reason will be because of variations in 'CT' clamp measurement circuits.
>
> An example: With a 5.0kW export limit in place, an Enphase gateway may measure precisely 5.0kW, but a Tesla battery gateway in the same install may measure the same power as 5.3kW. If the sensor value used for automated dampening is from the Tesla gateway in this circumstance then make sure 5.3 is the export limit specified.

##### Initial activation

For automated dampening to operate it must have access to a minimum set of data. Generation history is immediately loaded from the sensor (or sensors) history, but estimated actual history from Solcast will first be received after midnight local time. Because of this, when the feature is first enabled it will almost certainly not immediately model any dampening factors.

(If it is a new installation where estimated actuals are obtained once then factors may be modelled immediately.)

> [!TIP]
>
> Most automated dampening messages are logged at `DEBUG` level, however messages indicating that dampening factors cannot yet be modelled (and the reason why) is logged at `INFO` level. If your minimum log level for the integration is `WARNING` or higher then you will not see these notifications.

##### Modifying automated dampening behaviour

Automated dampening will suit many people, yet there are situations where it will not suit as implemented. For these situations modification of behaviour may be desired by advanced users.

At the core of automated dampening is that a PV generation value must be a reliable measurement when compared to estimated actual generation. If this is not reliable, because of artificial curtailment (limiting) then automated dampening needs to know that this is occurring. For simple utility export limiting to a fixed export value this is straightforward and is a built-in feature, but it is also possible to indicate that PV generation in a given interval is unreliable based on more complex circumstances.

This is where you can get creative with a specifically named templated sensor to cause PV generation intervals to be ignored when they cannot be relied upon to be accurate (i.e. not at "full" production).

Example scenarios include not being able to export to the grid, or choosing not to export. At these times, household consumption will match generation, and will confuse automated dampening.

To modify the behaviour of automated dampening, a template entity can be created with the name of `solcast_suppress_auto_dampening`. This can be using either the platform "sensor" or "binary_sensor".

The integration will monitor this entity for state changes. When a state is one of "on", "1", "true" or "True" at _any time in a half-hourly PV generation interval_ then this will signal automated dampening to vary its behaviour and exclude that interval, or if the entity state is one of "off", "0", "false" or "False" for the _entire interval_, the interval will be included as normal in automated dampening.

This entity _must_ begin and end each day in a state that is considered 'off', so rigging a sensor value of always 'on' will break things. State must change throughout the day, or be permanently 'off', and _never_ permanently 'on'.

Its suppression is also complementary to that provided by site export limit detection, so those configuration aspects should likely be removed, or carefully considered.

It also must have state change history to make any sense, so getting started will take time. This is a capability where you will need to inject common sense, and patience.

Here is a likely implementation sequence:

* 1. Create the templated `solcast_suppress_auto_dampening` entity.
* 2. Turn off automated dampening because it will be broken and confusing (but it was already broken and confusing before because you can't export or choose not to because negative wholesale price.)
* 3. Delete your `/config/solcast-generation.json` file. Any history is likely going to taint automated dampening results.
* 4. Ensure that recorder is configured with `purge_keep_days` of at least seven. When automated dampening is enabled it will attempt to load up to seven days of generation history. Let it when the time comes. If you usually purge more aggressively then it can always be changed back in a week. (You do not need to disable acquisition of estimated actuals.)
* 5. Completely restart HA to enable the recorder setting and get the Solcast integration to understand that generation data is now missing.
* 6. Wait patiently for one week to build history for the new entity.
* 7. Turn on automated dampening and watch it do its thing with your adaptation entity.

Having `DEBUG` level logging enabled for the integration will expose what happens, and this is a sensible thing to do while getting this set up. If you want any assistance then having the logs to hand, and sharing them will be _essential_.

##### Automated dampening notes

A modelled factor of greater than 0.95 is considered insignificant and is ignored. Feedback is welcomed as to whether these small factors should be significant and utilised.

These small factors would be corrected based on forecasted generation, so a case could be made to not ignore them. However a small and regular deviation from forecast is likely due to rooftop site misconfiguration or seasonal drift, and not shading.

The aim of automated dampening is not to correct for Solcast rooftop site misconfiguration, nor panel type generation quirks, nor improve forecasting. The aim is to detect consistently poor actual generation against that which is forecasted because of local factors.

> [!TIP]
>
> If you have two weeks of history data accumulated, and dampening factors are being generated for every half-hourly period when the sun is up then it is almost certain that you have a configuration issue somewhere. Generation is never matching the estimated actual generation, and it is likely that your Solcast rooftop site configuration is wrong.

Any rooftop site misconfiguration can have a significant impact on reported forecast, but that should be corrected in the rooftop site configuration. It is highly recommended to prove that the configuration is correct, and that forecasts are reasonably accurate on good generation days before attempting to configure automated dampening. Said in another way, if questionable forecasting is apparent then disable automated dampening before diagnosing the questionable forecasting.

The adjustments made by automated dampening may hinder efforts to resolve basic misconfiguration issues, and if it is enabled then reporting an issue of deviation from forecast where automated dampening is not implicated will likely impede issue resolution.

We all don't want that.

External energy sensors (like PV export and site export) must have a unit of measurement of mWh, Wh, kWh or MWh, and must cumulatively increase throughout a given day. If a unit of measurement cannot be determined then kWh is assumed. Other units like GWh or TWh do not make sense to use in a residential setting, and if used would result in an unacceptable loss of precision when converted to kWh so are unsupported. Other energy units like Joules and calories are also not supported, being uncommon units to use for electricity.

##### Feedback
Your feedback regarding experience with the automated dampening feature will be most welcome in the integration repository discussions.

Comprehensive logging at `DEBUG` level happens when automated dampening is enabled, and you are encouraged to examine and include that logged detail in any discussion that might point out a deficiency, experience (both positive and negative!), or an improvement opportunity.

#### Simple hourly dampening

You can change the dampening factor value for any hour. Values from 0.0 - 1.0 are valid. Setting 0.95 will dampen (reduce) each Solcast forecast data value by 5%. This is reflected in the sensor values and attributes and also in the Home Assistant Energy dashboard.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/reconfig.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/reconfig.png)

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/damp.png" width="500">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/damp.png)

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/dampopt.png" width="500">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/dampopt.png)

> [!TIP]
>
> 
> Most users of dampening configuration do not enter values in the configuration settings directly. Rather, they build automations to set values that are appropriate for their location at different days or seasons, and these call the `solcast_solar.set_dampening` action.
>
> 
> Factors causing dampening to be appropriate might be when different degrees of shading occur at the start or end of a day in different seasons, when the sun is close to the horizon and might cause nearby buildings or trees to cast a long shadow.

#### Granular dampening

Setting dampening for individual Solcast sites or using half-hour intervals is possible. This requires use of either the `solcast_solar.set_dampening` action, or creation/modification of a file in the Home Assistant config folder called `solcast-dampening.json`.

The action accepts a string of dampening factors, and also an optional site resource ID. (The optional site may be specified using either hyphens or underscores.) For hourly dampening supply 24 values. For half-hourly 48. Calling the action creates or updates the file `solcast-dampening.json` when either a site or 48 factor values are specified. If setting overall dampening with 48 factors, then an optional 'all' site may be specified (or simply omitted for this use case).

```yaml
action: solcast_solar.set_dampening
data:
  damp_factor: 1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1
  #site: 1234-5678-9012-3456
```

If a site resource ID is not specified, and 24 dampening values are given then granular dampening will be removed, and the overall configured hourly dampening will apply to all sites. (Granular dampening may also be disabled using the integration `CONFIGURE` dialogue.)

The action need not be called. Rather, the file itself may be updated directly and if created or modified will be read and used. Create/update/delete operations for this file are monitored, and resulting changes to the dampened forecast will be reflected in less than one second after the file operation occurs.

If granular dampening is configured for a single site in a multi-site set up then that dampening will only apply to the forecasts for that site. Other sites will not be dampened.

Dampening for all individual sites may of course be set, and when this is the case all sites must specify the same number of dampening values, either 24 or 48.

<details><summary><i>Click for examples of dampening files</i></summary>

The following examples can be used as a starter for the format for file-based granular dampening. Make sure that you use your own site resource IDs rather than the examples. The file should be saved in the Home Assistant config folder and named `solcast-dampening.json`.

Example of hourly dampening for two sites:

```yaml
{
  "1111-aaaa-bbbb-2222": [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0],
  "cccc-4444-5555-dddd": [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]
}
```

Example of hourly dampening for a single site:

```yaml
{
  "eeee-6666-7777-ffff": [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]
}
```

Example of half-hourly dampening for two sites:

```yaml
{
  "8888-gggg-hhhh-9999": [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0],
  "0000-iiii-jjjj-1111": [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]
}
```

Example of half-hourly dampening for all sites:

```yaml
{
  "all": [1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0]
}
```
</details>

#### Reading forecast values in an automation

The action `solcast_solar.query_forecast_data` can return both dampened and undampened forecasts (include `undampened: true`). The site may also be included in the action parameters if a breakdown is desired. (The optional site may be specified using either hyphens or underscores.)

```yaml
action: solcast_solar.query_forecast_data
data:
  start_date_time: 2024-10-08T12:00:00+11:00
  end_date_time: 2024-10-08T19:00:00+11:00
  undampened: true
  #site: 1111-aaaa-bbbb-2222
```

Un-dampened forecast history is retained for just 14 days.

#### Reading estimated actual values in an automation

When calculating dampening using an automation it may be beneficial to use estimated actual past values as input.

This is possible by using the action `solcast_solar.query_estimate_data`. The site may not be included in the action parameters presently. (If a site breakdown is desired, then raise an issue or a discussion topic.)

```yaml
action: solcast_solar.query_estimate_data
data:
  start_date_time: 2024-10-08T12:00:00+11:00
  end_date_time: 2024-10-08T19:00:00+11:00
```

Estimated actual data is retained for 730 days.

#### Reading dampening values

The currently set dampening factors may be retrieved using the action "Solcast PV Forecast: Get forecasts dampening" (`solcast_solar.get_dampening`). This may specify an optional site resource ID, or specify no site or the site 'all'. Where no site is specified then all sites with dampening set will be returned. An error is raised should a site not have dampening set.

The optional site may be specified using either hyphens or underscores. If the service call uses underscores, then the response will also use underscores.

If granular dampening is set to specify both individual site dampening factors and "all" sites dampening factors, then attempting retrieval of an individual site dampening factors will result in the "all" sites dampening factors being returned, with the "all" site being noted in the response. This is because an "all" set of dampening factors overrides the individual site settings in this circumstance.

Example call:

```yaml
action: solcast_solar.get_dampening
data:
  site: b68d-c05a-c2b3-2cf9
```

Example response:

```yaml
data:
  - site: b68d-c05a-c2b3-2cf9
    damp_factor: >-
      1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0
```

### Sensor attributes configuration

There are quite a few sensor attributes that can be used as a data source for template sensors, charts, etc., including a per-site breakdown, estimate 10/50/90 values, and per-hour and half hour detailed breakdown for each forecast day.

Many users will not use these attributes, so to cut the clutter (especially in the UI and also database statistics storage) generation all of these can be disabled if they are not needed.

By default, all of them are enabled, except for per-site detailedForecast and detailedHourly. (All hourly and half-hourly detail attributes are excluded from being sent to the Home Assistant recorder, as these attributes are very large, would result in excessive database growth, and are of little use when considered long-term.)

> [!NOTE]
>
> 
> If you want to implement the sample PV graph below then you'll need to keep half-hourly detail breakdown enabled, along with `estimate10`.

### Hard limit configuration

There is an option to set a "hard limit" for projected inverter output, and this limit will 'clip' the Solcast forecasts to a maximum value.

The hard limit may be set as an "overall" value (applying to all sites in all Solcast accounts configured), or it may be set by Solcast account with a separate hard limit value for each API key. (In the latter case, comma-separate the desired hard limit values.)

The scenario requiring use of this limit is straightforward but note that hardly any PV installations will need to do so. (And if you have micro-inverters, or one inverter per string then definitely not. The same goes for all panels with identical orientation in a single Solcast site.)

Consider a scenario where you have a single 6kW string inverter, and attached are two strings each of 5.5kW potential generation pointing in separate directions. This is considered "over-sized" from an inverter point of view. It is not possible to set an AC generation limit for Solcast that suits this scenario when configured as two sites, as in the mid-morning or afternoon in Summer a string may be generating 5.5kW DC, with 5kW AC resulting, and the other string will probably be generating as well. So setting an AC limit in Solcast for each string to 3kW (half the inverter) does not make sense. Setting it to 6kW for each string also does not make sense, as Solcast will almost certainly over-state potential generation.

The hard limit may be set in the integration configuration or set by using the service action `solcast_solar.set_hard_limit` in `Developer Tools`. To disable the hard limit enter a value of zero or 100 in the configuration dialogue. To disable using a service action call use `solcast_solar.remove_hard_limit`. (Zero cannot be specified when performing the set action.)

### Excluded sites configuration

It is possible to exclude one or more Solcast sites from the calculation of sensor totals and the Energy dashboard forecast.

The use case is to allow a local "main" site or sites to be the overall combined forecast values, and a "remote" site to be visualised separately with Apex charts and/or template sensors that get their value from site breakdown sensor attributes. Note that it is not possible to build a separate Energy dashboard feed from templated sensors (this data comes directly from the integration as a data dictionary).

Utilising this advanced feature alongside template sensors and Apex charts is not a simple thing, however examples are provided throughout the readme for both templated sensors built from attribute data, and for an Apex chart. See [Interacting](#interacting), [Sample template sensors](#sample-template-sensors) and [Sample Apex chart for dashboard](#sample-apex-chart-for-dashboard).

Configuration is by way of the `CONFIGURE` dialogue.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/ExcludeSites1.png" width="500">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/ExcludeSites1.png)

Selecting sites to exclude and clicking `SUBMIT` will take effect immediately. It is not required to wait for a forecast update.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/ExcludeSites2.png" width="500">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/ExcludeSites2.png)

> [!NOTE]
>
> 
> The site names and resource IDs are sourced from the sites that are known at the time of last sites fetch from Solcast (this is at startup). It is not possible to both add a new API key and select a site to exclude from the new account being added. The new account must first be added, which will cause the integration to restart and load the new sites. After that the sites to exclude from the new account may be selected.

### Advanced configuration options

It is possible to change the behaviour of some integration functions, most notably for integrated automated dampening.

These options may be set by creating a file called `solcast-advanced.json` in the Home Assistant configuration directory (usually `/config`).

For the available options, see the documentation at [Advanced options](https://github.com/BJReplay/ha-solcast-solar/blob/main/ADVOPTIONS.md).

## Sample template sensors

### Combining site data

A potential desire is to combine the forecast data for multiple sites common to a Solcast account, enabling visualisation of individual account detailed data in an Apex chart.

This code is an example of how to do so by using a template sensor, which sums all pv50 forecast intervals to give a daily account total, plus builds a detailedForecast attribute of all combined interval data to use in a visualisation.

Site breakdowns must be enabled in the integration options (the detailed forecast breakdown is not enabled by default).

**Reveal code**
<details><summary><i>Click here</i></summary>

```yaml
template:
  - sensor:
      - name: "Solcast Combined API 1"
        unique_id: "solcast_combined_api_1"
        state: >
          {% set sensor1 = state_attr('sensor.solcast_pv_forecast_forecast_today', 'b68d_c05a_c2b3_2cf9') %}
          {% set sensor2 = state_attr('sensor.solcast_pv_forecast_forecast_today', '83d5_ab72_2a9a_2397') %}
          {{ sensor1 + sensor2 }}
        unit_of_measurement: "kWh"
        attributes:
          detailedForecast: >
            {% set sensor1 = state_attr('sensor.solcast_pv_forecast_forecast_today', 'detailedForecast_b68d_c05a_c2b3_2cf9') %}
            {% set sensor2 = state_attr('sensor.solcast_pv_forecast_forecast_today', 'detailedForecast_83d5_ab72_2a9a_2397') %}
            {% set ns = namespace(i=0, combined=[]) %}
            {% for interval in sensor1 %}
              {% set ns.combined = ns.combined + [
                {
                  'period_start': interval['period_start'].isoformat(),
                  'pv_estimate': (interval['pv_estimate'] + sensor2[ns.i]['pv_estimate']),
                  'pv_estimate10': (interval['pv_estimate10'] + sensor2[ns.i]['pv_estimate10']),
                  'pv_estimate90': (interval['pv_estimate90'] + sensor2[ns.i]['pv_estimate90']),
                }
              ] %}
              {% set ns.i = ns.i + 1 %}
            {% endfor %}
            {{ ns.combined | to_json() }}
```
</details>

## Sample Apex chart for dashboard

The following YAML produces a graph of today's PV generation, PV forecast and PV10 forecast. Requires [Apex Charts](https://github.com/RomRider/apexcharts-card) to be installed.

[<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/forecast_today.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/forecast_today.png)

Customise with appropriate Home Assistant sensors for today's total solar generation and solar panel PV power output.

> [!NOTE]
>
> 
> The chart assumes that Solar PV sensors are in kW, but if some are in W, add the line `transform: "return x / 1000;"` under the entity id to convert the sensor value to kW.

**Reveal code**
<details><summary><i>Click here</i></summary>

```yaml
type: custom:apexcharts-card
header:
  title: Solar forecast
  show: true
  show_states: true
  colorize_states: true
apex_config:
  chart:
    height: 300px
  tooltip:
    enabled: true
    shared: true
    followCursor: true
graph_span: 24h
span:
  start: day
yaxis:
  - id: capacity
    show: true
    opposite: true
    decimals: 0
    max: 100
    min: 0
    apex_config:
      tickAmount: 10
  - id: kWh
    show: true
    min: 0
    apex_config:
      tickAmount: 10
  - id: header_only
    show: false
series:
  - entity: sensor.SOLAR_POWER
    name: Solar Power (now)
    type: line
    stroke_width: 2
    float_precision: 2
    color: Orange
    yaxis_id: kWh
    unit: kW
    extend_to: now
    show:
      legend_value: true
      in_header: false
    group_by:
      func: avg
      duration: 5m
  - entity: sensor.solcast_pv_forecast_forecast_today
    name: Forecast
    color: Grey
    opacity: 0.3
    stroke_width: 0
    type: area
    time_delta: +15min
    extend_to: false
    yaxis_id: kWh
    show:
      legend_value: false
      in_header: false
    data_generator: |
      return entity.attributes.detailedForecast.map((entry) => {
            return [new Date(entry.period_start), entry.pv_estimate];
          });
  - entity: sensor.solcast_pv_forecast_forecast_today
    name: Forecast 10%
    color: Grey
    opacity: 0.3
    stroke_width: 0
    type: area
    time_delta: +15min
    extend_to: false
    yaxis_id: kWh
    show:
      legend_value: false
      in_header: false
    data_generator: |
      return entity.attributes.detailedForecast.map((entry) => {
            return [new Date(entry.period_start), entry.pv_estimate10];
          });
  - entity: sensor.SOLAR_GENERATION_ENERGY_TODAY
    yaxis_id: header_only
    name: Today Actual
    stroke_width: 2
    color: Orange
    show:
      legend_value: true
      in_header: true
      in_chart: false
  - entity: sensor.solcast_pv_forecast_forecast_today
    yaxis_id: header_only
    name: Today Forecast
    color: Grey
    show:
      legend_value: true
      in_header: true
      in_chart: false
  - entity: sensor.solcast_pv_forecast_forecast_today
    attribute: estimate10
    yaxis_id: header_only
    name: Today Forecast 10%
    color: Grey
    opacity: 0.3
    show:
      legend_value: true
      in_header: true
      in_chart: false
  - entity: sensor.solcast_pv_forecast_forecast_remaining_today
    yaxis_id: header_only
    name: Remaining
    color: Grey
    show:
      legend_value: true
      in_header: true
      in_chart: false
```
</details>


## Known issues

* Altering hard limit will alter recorded forecast history. This is currently by design and may not change.
* Sample sites (if set up in your Solcast dashboard) will be included in your forecasts retrieved by this integration and returned to Home Assistant.
<details>
    If you see sample sites (such as these [<img src="https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SampleSites.png">](https://github.com/BJReplay/ha-solcast-solar/blob/main/.github/SCREENSHOTS/SampleSites.png)) remove them from your Solcast dashboard.
</details>

## Troubleshooting

<details><summary><i>Click here to expand troubleshooting tips.</i></summary>

This integration aims to log very little when things are working fine. When issues occur `ERROR` or `CRITICAL` log entries will be produced, and when temporary or minor issues occur then `WARNING` entries. Always check the logs as the first step in troubleshooting an issue.

To enable greater detail for logging, many entries are issued at `DEBUG` level. Enabling debug logging as an aid to troubleshooting is advised. Note that changing the log level will require a Home Assistant restart, which will rename the current `homeassistant.log` file to `homeassistant.log.1` (there is no `.2`, so only this session and the prior session are accessible.)

In `/homeassistant/configuration.yaml`:

```
logger:
  default: warn
  logs:
    custom_components.solcast_solar: debug
```

Reviewing logs is quite simple, but debug logs cannot be reviewed from the UI. The file `/homeassistant/home-assistant.log` must be viewed. From an SSH session use `less /homeassistant/home-assistant.log`. You may have other ways to view this file depending on the add-ons installed.

### API key issues

During configuration you enter an API key (or keys), and the sites configured at solcast.com will be retrieved at this time to test the key. A failure generally falls into a limited number of categories. The key is incorrect, or the Solcast account has no sites configured, or solcast.com cannot be reached. These situations are mostly self-evident.

In the event that solcast.com cannot be reached you should generally look elsewhere for issues. If a transient condition occurs, like receiving a `429/Try again later` error, then literally follow the instruction by waiting, then trying initial setup again. (The Solcast site generally gets swamped with requests on fifteen minute time boundaries, and mostly at the top of each hour.)

### Forecast update issues

When a forecast update occurs, the integration incorporates a retry mechanism to cope with transient `429/Try again later` situations. It is very rare that all ten attempts fail, however it has been known to happen early in the European morning. If it does happen, then the next update will almost certainly succeed.

An API usage counter is maintained to track the number of calls made to solcast.com each day (which begins at UTC midnight). If this counter is mis-aligned with reality then upon encountering an API call refusal it will be set to its maximum value, and not reset until UTC midnight.

### Forecasted values look "just wrong"

There may still be demo sites configured at solcast.com. Check this, and if they are still configured then delete them.

Double check your azimuth/tilt/location and other settings for sites also. "Just wrong" values are not caused by the integration, rather are a symptom that something is wrong with the overall set up.

### Exceptions in logs

Exceptions should never be logged unless something is seriously wrong. If they are logged then they are usually a symptom of the underlying cause, not a code defect, and generally not directly related to the root cause of any issue. Look to potential causes being something that has changed.

When exceptions occur it is likely that sensor states will become `Unavailable`, which is also a symptom of an exception occurring.

If you are "upgrading" from a very old or completely different Solcast integration then this is not an "upgrade". It is a migration, so view it as such. Some migration scenarios are covered, but others may require complete removal of all incompatible data that may be causing serious issues. See [Complete integration removal](#complete-integration-removal) to get an understanding of the location of some files that may be interfering.

That said, code defects can happen, but they should not be the first suspicion. Extensive automated testing of this code is done using PyTest before a release, with the tests covering a vast range of scenarios and executing every line of code. Some of these tests do expect the worst regarding situations that can cause exceptions, like corruption of cached data, and in these situations exceptions are expected.

### Final word

If behaviour most odd is encountered, filled with exceptions occurring, then a quick fix may be to back up all `/homeassistant/solcast*.json` files, remove them, and then restart the integration.
</details>

## Complete integration removal

To completely remove all traces of the integration start with navigating to `Settings` | `Devices & Services` | `Solcast PV Forecast`, click the three dots next to the gear icon (`CONFIGURE` in early HA releases) and select `Delete`.

At this point the configuration settings have been reset, but the code and forecast information caches will still exist (setting up the integration again will re-use this cached data, which may or may not be desirable).

The caches reside in the Home Assistant configuration folder (usually `/config/` or `/homeassistant/`, but its location can vary based on Home Assistant deployment type). These files are named after the integration, and may be removed with `rm solcast*.json`.

The code itself resides at `/config/custom_components/solcast_solar`, and removing this entire folder will complete the total removal of the integration.

## Changes

v4.4.7

* Add advanced options configuration file by @autoSteve
* Add attribute `custom_hours` to `Forecast Next X Hours` sensor by @autoSteve
* Auto-dampen, improve interval unreliable generation exclusion by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.4.6...v4.4.7

v4.4.6

* Fix: Auto-dampen, ignore generation days with a small number of history samples by @autoSteve
* Fix: Restrict auto-dampen modelling to 14 days (it was up to generation history) by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.4.5...v4.4.6

v4.4.5

* Europe/Dublin transition between standard/Winter time accommodated by @autoSteve
* Auto-dampen, utilise inter-quartile anomaly detection for generation entities by @autoSteve
* Auto-dampen, adapt to generation-consistent or time-consistent generation entities by @autoSteve
* Auto-dampen, ignore entire generation intervals having anomalies by @autoSteve
* Auto-dampen, minimum number of matching intervals must be greater than one by @autoSteve
* Auto-dampen, add generation suppression entity support by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.4.4...v4.4.5

v4.4.4

* Fix: Auto-dampen, daylight time adjusted interval by @rcode6 and @autoSteve
* Remove and suppress ignored unusual azimuth issues by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.4.3...v4.4.4

v4.4.3

* Randomised actuals fetch then immediate auto-dampen modelling by @autoSteve
* Exclude disabled auto-dampen entities from selection by @autoSteve
* Auto-dampen, exclude export-limited intervals from all days by @autoSteve
* Auto-dampen, daylight time transitions handled by @autoSteve
* Fetch up to fourteen days of forecast data by @autoSteve
* Fix: Update TEMPLATES.md dampening factors chart by @jaymunro
* Fix: Update TEMPLATES.md typo in sensor name by @gcoan
* Minimum HA version 2025.3

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.4.2...v4.4.3

v4.4.2

* Auto-dampen, accommodate periodically updating generation entities (Envoy) by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.4.1...v4.4.2

v4.4.1

* Generation/export unit of measurement automatic adjustment by @brilthor and @autoSteve
* Ignore atypical generation entity jumps by @autoSteve
* Require a majority of "good day" actuals generation agreement for auto-dampening by @autoSteve
* Add auto-dampening chart example of applied vs. base to TEMPLATES.md by @Nilogax. Thanks!
* Extensive auto-dampening README.md updates by @autoSteve, @gcoan and @Nilogax. Thanks!
* Fix: Migration of usage without reset, key change no sites change by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.4.0...v4.4.1

v4.4.0
* Add auto-dampening feature by @autoSteve
* Modified dampening factors are applied from start of current day by @autoSteve
* Fix for translated sensors max attr size exceeded by @autoSteve
* Monitor solcast-dampening.json for create/update/delete by @autoSteve
* Add last_attempt attribute to api_last_polled entity by @autoSteve
* Add allow action site parameter with hyphen or underscore by @autoSteve
* Add test for unusual azimuth by @autoSteve
* Fix Energy dashboard start/end points by @autoSteve
* Attribution attributes only where credit is due by @autoSteve
* Minimum HA version 2024.11

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.3.5...v4.4.0

### Prior changes
<details><summary><i>Click here for changes back to v3.0</i></summary>

v4.3.5
* Fix API key change detection on 429 when using multi-key by @autoSteve
* Fix key validation corner case that could prevent start by @autoSteve
* Add update failure count attributes to last polled sensor by @autoSteve
* Allow get sites when failed every 30 minutes in 429 storm by @autoSteve
* Stricter type checking by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.3.4...v4.3.5

v4.3.4
* Include rooftop site tags in site sensor attributes by @autoSteve
* Remove annoying startup debug logged at critical level by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.3.3...v4.3.4

v4.3.3
* Add sites to exclude from totals and Energy dashboard by @autoSteve
* Add Portuguese translation by @ViPeR5000 (thanks!)
* Clean up orphaned hard limit diagnostic sensors by @autoSteve
* Avoid init crash HA restart calling rooftop_sites repeatedly by @autoSteve
* Fix diagnostic sensor values for multi-api key hard limit by @autoSteve
* Fix remove orphaned cache where API key contains non-alphanumeric characters by @autoSteve
* Fix solcast-dampening.json granular dampening formatting to be semi-indented by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.3.2...v4.3.3

v4.3.2
* Replace hyphen with underscore for site breakdown attribute names by @autoSteve
* Add Spanish translation by @autoSteve
* Add Italian translation by @Ndrinta (thanks!)

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.3.1...v4.3.2

v4.3.1
* Add HACS Default installation instructions by @BJReplay

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.3.0...v4.3.1

v4.3.0
* Fix an issue when half-hourly breakdown is disabled but hourly is enabled by @autoSteve
* Fix an issue with transitioning from granular to legacy dampening by @autoSteve
* Fix an issue with using multiple hard limits by @autoSteve
* Fix an issue with stale start when auto-update is enabled by @autoSteve
* Add auto-update attributes to api_last_polled by @autoSteve
* Upgrade data files from v3 integration schema by @autoSteve
* Config and options flows check valid API key and sites available by @autoSteve
* Add re-auth and reconfigure flows by @autoSteve
* Add repair flows for forecasts not updating by @autoSteve
* Fetch estimated actuals on super-stale start by @autoSteve
* Set sensors to unavailable on integration failure by @autoSteve
* Catch duplicate API key being specified by @autoSteve
* Remove check for conflicting integration by @autoSteve
* Add integration and unit tests by @autoSteve
* Strict type checking by @autoSteve
* Add troubleshooting section in README.md by @autoSteve
* Fix an issue of incorrect forecasts with notes to remove any sample sites from Solcast dashboard by @BJReplay
* Updated issue template by @BJReplay

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.2.7...v4.3.0

v4.2.7
* Fix an issue with API key validation by @autoSteve
* Fix an issue preventing clean integration removal by @autoSteve
* Improve check for conflicting integration by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.2.6...v4.2.7

v4.2.6
* Fix an issue that was preventing new installs by @autoSteve
* Fix an issue calculating auto-update interval for multi-API key by @autoSteve
* Fix an issue migrating from/to multi-API for Docker setup by @autoSteve
* Fix an issue clearing all forecast history by @autoSteve
* Fix an issue where API count was not incremented on stale start fetch by @autoSteve
* Fix an issue where API used/total & last updated sensors were not updated by @autoSteve
* Add Solcast API simulator to support development and accelerate testing by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.2.5...v4.2.6

v4.2.5
* Add multi-API key hard limit by @autoSteve
* Proportionally limit site breakdowns by @autoSteve
* Calculate daily site tally correctly based on hard limit by @autoSteve
* Immediate application of dampening to future forecasts by @autoSteve
* Fix daylight time transition issues by @autoSteve
* Fix system health output exception by @autoSteve
* Logging improvements for info situational awareness by @autoSteve
* Auto-update tolerate restart right before scheduled fetch by @autoSteve
* Update Polish translation, with thanks to @erepeo

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.2.4...v4.2.5

v4.2.4
* Add user-agent header to API calls by @autoSteve
* Refer to action instead of service call by @gcoan

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.2.3...v4.2.4

v4.2.3
* Fix an issue that causes changing Solcast accounts to fail by @autoSteve
* Fix an issue with multi-API key where API usage reset was not handled correctly by @autoSteve
* Fix an issue with enabled detailed site breakdown for hourly attributes by @autoSteve
* Code clean-up and some refactoring by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.2.0...v4.2.3

v4.2.1 / v4.2.2
* Releases pulled due to issue

v4.2.0
* Generally available release of v4.1.8 and v4.1.9 pre-release features
* Translations of service call error responses by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.1.7...v4.2.0

Most recent changes: https://github.com/BJReplay/ha-solcast-solar/compare/v4.1.9...v4.2.0

v4.1.9 pre-release
* Granular dampening to dampen per half hour period by @autoSteve and @isorin
* Dampening applied at forecast fetch and not to forecast history by @autoSteve and @isorin
* Retrieve un-dampened forecast values using service call by @autoSteve (thanks @Nilogax)
* Get presently set dampening factors using service call by @autoSteve (thanks @Nilogax)
* Migration of un-dampened forecast to un-dampened cache on startup by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.1.8...v4.1.9

v4.1.8 pre-release
* Automated forecast updates that do not require an automation by @autoSteve and @BJReplay
* Add per-site dampening by @autoSteve
* Add site breakdown option for detailed forecasts by @autoSteve
* Add hard limit configuration to options by @autoSteve
* Suppress integration reload when many configuration options are changed by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.1.7...v4.1.8

v4.1.7
* Fix issues with site breakdown for sites added at a later date by @autoSteve
* Fix issues with site breakdown for splined sensors by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.1.6...v4.1.7

v4.1.6
* Simplify configure dialogue by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.1.5...v4.1.6

v4.1.5 pre-release
* Bug: Timestamp stored in usage cache was wrong by @autoSteve
* Bug: Adding API key reset usage for first key by @autoSteve
* Bug: Missing iterator in new sites check by @autoSteve
* Work around a possible HA scheduling bug by @autoSteve
* Code style alignment to HA style guidelines by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.1.4...v4.1.5

v4.1.4 pre-release
* Update Polish translation by @home409ca
* Rename integration in HACS to Solcast PV Forecast by @BJReplay
* Reduce aiofiles version requirement to >=23.2.0 by @autoSteve
* Configuration dialog improvements by @autoSteve
* Misc translation updates by @autoSteve
* Refactor moment and remaining spline build by @autoSteve
* Prevent negative forecast for X hour sensor by @autoSteve
* Suppress spline bounce for reducing spline by @autoSteve
* More careful serialisation of solcast.json by @autoSteve
* Monitor last updated timestamp for sites-usage.json by @autoSteve
* Extensive code clean-up by @autoSteve
 
Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.1.3...v4.1.4

v4.1.3
* Accommodate the removal of API call GetUserUsageAllowance by @autoSteve
* Halve retry delays by @autoSteve
* Readme improvements by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.1.2...v4.1.3

v4.1.2
* Fifteen minute shift, because 30-minute averages by @autoSteve
* Increase forecast fetch attempts to ten by @autoSteve
* Move images to screenshots by @BJReplay
* Fix readme images not displaying in HACS frontend

Replaces v4.1.1

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.1.0...v4.1.2

v4.1
* First major release since v4.0.31 that wasn't tagged as a pre-release
* Those other releases have mostly been pretty stable, but we're confident that this release is ready for everyone
* Changes since v4.0.31:
  * Greatly improved stability for all, and initial start-up experience for new users
  * Additional sensor attributes
  * New configuration options to suppress sensor attributes
  * Redaction of sensitive information in debug logs
  * Improved efficiency, with many sensors calculated in five-minute intervals, some only when forecasts are fetched
  * Spline interpolation for ‘momentary’ and ‘period’ sensors
  * Fixes for multi-API key users
  * Fixes for Docker users
  * Exception handling improvements
  * Logging improvements
* @autoSteve is welcomed as a CodeOwner
* It is now apparent that it is unlikely that this repo will be added as a default repo in HACS until HACS 2.0 is out, so the installation instructions make it clear that adding via the Manual Repository flow is the preferred approach, and new instructions have been added to show how to do this.

Release Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.31...v4.1.0

Most recent changes: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.43...v4.1.0

v4.0.43
* Auto-fetch on startup when stale forecast data is detected by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.42...v4.0.43

v4.0.42
* Initial sites load fail reporting and HA auto-retries by @autoSteve
* Suppress spline bounce in moment splines by @autoSteve
* Recalculate splines at midnight before sensors update by @autoSteve
* Readme updates by @autoSteve
* Dampening and hard limit removed from per-site forecast breakdowns (too hard, too misleading) by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.41...v4.0.42

v4.0.41
* Interpolated forecast 0/30/60 fix #101 by @autoSteve
* Ensure config directory is always relative to install location #98 by @autoSteve
* Add state_class to `power_now_30m` and `power_now_1hr` to match `power_now` by @autoSteve (will remove LTS, but LTS is not useful for these sensors)
* Utilise daily splines of momentary and reducing forecast values by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.40...v4.0.41

v4.0.40
* Interpolated forecast 0/30/60 power and energy X hours by @autoSteve
* Ensure config directory is always relative to install location by @autoSteve
* Sample PV chart enhancements by @gcoan

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.39...v4.0.40

v4.0.39
* Updates to sensor descriptions, and alter some sensor names by @isorin (Potentially breaking for UI/automations/etc. should these these sensors be in use. Power in 30/60 minutes, and custom X hours sensor.)
* Remove dependency on scipy library by @autoSteve
* Add granular configuration options for attributes by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.38...v4.0.39

v4.0.38
* Add Solcast key concepts and sample PV generation graph to readme by @gcoan
* Add PCHIP spline to forecast remaining by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.37...v4.0.38

v4.0.37
* Alter attribute naming to remove "pv_" by @autoSteve (note: breaking if new attributes have already been used in templates/automations)
* Sensor attribute rounding #51 by @autoSteve
* Improve exception handling for forecast fetch by @autoSteve
* Further improve exception handling for forecast fetch by @autoSteve
* Replace exception with a warning #74 by @autoSteve
* Retry an unexplained cache/initial data load by @autoSteve
* Less shouty debug logging by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.36...v4.0.37

v4.0.36
* (Enhancement) Additional sensor attributes (estimate/estimate10/estimate90) and logging improvements by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.35...v4.0.36

v4.0.35
* (Enhancement) Breakdown of individual site forecast wattage and time as attributes by @autoSteve
* Do not log options version upgrade if no upgrade is required by @autoSteve
* Add info about preserving oziee history and config to banner by @iainfogg

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.34...v4.0.35

v4.0.34
* Fix query_forecast_data so that near-term historical forecasts are returned by @isorin
* Instantly fall-back to cache on reload if rooftop/usage API calls fail, which can reduce start time by @autoSteve
* An async call timeout of sites get will fall back to cache if it exists by @autoSteve
* Much logging improvements by @autoSteve
* Sites cache being sometimes incorrectly created with the API key appended, despite only having one API key by @autoSteve
* Redaction of latitude/longitude in debug logs by @autoSteve
* Likely elimination of 'tally' warnings by @autoSteve
* Fix API usage retry mechanism by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.33...v4.0.34

v4.0.33
* Performance improvements for sensor updates by @isorin, including:
  * Reduced the update interval of sensors to 5 minutes
  * Split the sensors into two groups: sensors that need to be updated every 5 minutes and sensors that need to be updated only when the data is refreshed or the date changes (daily values)
  * Fixed issues with removing the past forecasts (older than 2 years), broken code
  * Improve the functionality of the forecasts, for example "forecast_remaining_today" is updated every 5 minutes by calculating the remaining energy from the current 30 minute interval. Same for "now/next hour" sensors.
* Redaction of Solcast API key in logs by @isorin
* Revert Oziee '4.0.23' async_update_options #54 by @autoSteve, which was causing dampening update issues

A comment from @isorin: "_I use the forecast_remaining_today to determine the time of the day when to start charging the batteries so that they will reach a predetermined charge in the evening. With my changes, this is possible._"

To that, I say nicely done.

New Contributors
* @isorin made their first contribution in https://github.com/BJReplay/ha-solcast-solar/pull/45

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.32...v4.0.33

v4.0.32
- Bug fix: Independent API use counter for each Solcast account by @autoSteve
- Bug fix: Force all caches to /config/ for all platforms (fixes Docker deployments) #43 by @autoSteve
- Improve forecast fetch/retry logging debug, info, warning choice by @autoSteve
- Suppression of consecutive forecast fetches within fifteen minutes (fixes strange multiple fetches should a restart occur exactly when automation for fetch is triggered) by @autoSteve
- Work-around: Prevent error when 'tally' is unavailable during retry by #autoSteve
- Fix for earlier HA versions not recognising version= for async_update_entry() #40 by autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.31...v4.0.32

v4.0.31
- docs: Changes to README.md
- docs: Add troubleshooting notes.
- docs: Combine Changes Notes from info.md into README.md
- docs: Set up so that HACS displays README.md

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.30...v4.0.31

v4.0.30
- Bug fix: Support multiple Solcast account sites caching
- Bug fix: Retry mechanism when rooftop sites gather is actually successful was broken

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.29...v4.0.30

v4.0.29
- Bug fix: Write API usage cache on every successful poll by @autoSteve in https://github.com/BJReplay/ha-solcast-solar/pull/29
- Bug fix: Default API limit to 10 to cope with initial call fail by @autoSteve
- Increase sites GET retries from two to three by @autoSteve

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.28...v4.0.29

v4.0.28
- Add retry for rooftop sites collection #12 by @autoSteve in https://github.com/BJReplay/ha-solcast-solar/pull/26
- Full info.md changes since v4.0.25
- Re-incorporate most v4.0.23 oziee changes by @autoSteve 
- Retain cached data when API limit reached

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.27...v4.0.28

New Collaborator

- @autoSteve has made a huge contribution over the last few days - he has a sponsor button on his profile, so don't be afraid to mash it!

v4.0.27
- docs: Update info.md by @Kolbi in https://github.com/BJReplay/ha-solcast-solar/pull/19
- Use aiofiles with async open, await data_file by @autoSteve in https://github.com/BJReplay/ha-solcast-solar/pull/21
- Add support for async_get_time_zone() by @autoSteve in https://github.com/BJReplay/ha-solcast-solar/pull/25

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.26...v4.0.27

New Contributors
- @Kolbi made their first contribution in https://github.com/BJReplay/ha-solcast-solar/pull/19
- @autoSteve made their first contribution in https://github.com/BJReplay/ha-solcast-solar/pull/21

v4.0.26
- Fixes #8 #9 #10 - My HA Button category by @mZ738 in https://github.com/BJReplay/ha-solcast-solar/pull/11
- Update README.md by @wimdebruyn in https://github.com/BJReplay/ha-solcast-solar/pull/5
- Prepare for new Release by @BJReplay in https://github.com/BJReplay/ha-solcast-solar/pull/13

Full Changelog: https://github.com/BJReplay/ha-solcast-solar/compare/v4.0.25...v4.0.26
 
New Contributors
* @mZ738 made their first contribution in https://github.com/BJReplay/ha-solcast-solar/pull/11
* @wimdebruyn made their first contribution in https://github.com/BJReplay/ha-solcast-solar/pull/5  

v4.0.25
- HACS Submission

v4.0.24
- More changes to remove links to https://github.com/oziee that were missed the first time around
- More changes to prepare to submit to HACS

v4.0.23
- Changed Owner to @BJReplay
- Changed Github Repo to https://github.com/BJReplay/ha-solcast-solar

v4.0.22
- this time weather sensor is gone.. and midnight UTC reset works
- (*)added a config for setting a hard limit for inverters with over sized solar arrays 
   *99.9999999% of users will not need to ever user and set this (0.00000001% is @CarrapiettM)

v4.0.21
- removed weather sensor as it keeps failing with errors

v4.0.20
- fixed the info error for `solcast_pv_forecast_forecast_today (<class 'custom_components.solcast_solar.sensor.SolcastSensor'>) is using state class 'measurement' which is impossible considering device class ('energy')`
- removed the midnight UTC fetch and replaced with set to zero to reduce the polling on Solcast system
⚠️ To help reduce impact on the Solcast backend, Solcast have asked that users set their automations for polling with a random min and sec timing.. if you are polling at say 10:00 set it to 10:04:10 for instance so that everyone is not polling the services at the same time

v4.0.19
- fix resetting api limit/usage not updating HA UI

v4.0.18
- fixed weather sensor value not persisting 
- reset the api limit and usage sensors at UTC midnight (reset usage)

v4.0.17
- updated Slovak translation thanks @misa1515
- added sensor for Solcast weather description

v4.0.16
- added @Zachoz idea of adding a setting to select which solcast estimate field value for the forecast calculations, either estimate, estimate10 or estimate90
    ESTIMATE - Default forecasts
    ESTIMATE10 = Forecasts 10 - cloudier than expected scenario  
    ESTIMATE90 = Forecasts 90 - less cloudy than expected scenario  

v4.0.15
- added custom 'Next X hours' sensor. You select the number of hours to be calculated as the sensor
- added French translation thanks to @Dackara
- added some sensors to be included in HA statistics data

v4.0.14
- changed attrib values from rooftop sites so pins are not added to maps (HA auto adds item to the map if attributes contain lat/long values)
- added Urdu thanks to @yousaf465

v4.0.13
- added Slovak translation thanks to @misa1515
- extended polling connection timeout from 60s to 120s
- added some more debug output points for data checking
- new forecast data attribute `dataCorrect` returns True of False if the data is complete for that day.
- removed `0 of 48` debug message for the 7th day forecast because if the api is not polled at midnight then the data is not complete for the 7th day (limitation of the max records Solcast returns)

v4.0.12
- HA 2023.11 beta forces sensors not to be listed under `Configuration`. The rooftop sensors have been moved to `Diagnostic`

v4.0.11
- better handling when data is missing pieces for some sensors

v4.0.10
- fixes for changing API key once one has previously been set

v4.0.9
- new service to update forecast hourly dampening factors

v4.0.8
- added Polish translation thanks to @home409ca
- added new `Dampening` to the Solcast Integration configuration

v4.0.7
- better handling when Solcast site does not return API data correctly

v4.0.6
- fixed divide by zero errors if there is no returned data
- fixed remaining today forecast value. now includes current 30min block forecast in the calculation

v4.0.5
- PR #192 - updated German translation.. thanks @florie1706
- fixed `Remaining Today` forecast.. it now also uses the 30min interval data
- fixed `Download diagnostic` data throwing an error when clicked

v4.0.4
- finished off the service call `query_forecast_data` to query the forecast data. Returns a list of forecast data using a datetime range start - end
- and thats all.. unless HA makes breaking changes or there is a major bug in v4.0.4, this is the last update

v4.0.3
- updated German thanks to @florie1706 PR#179 and removed all other localisation files
- added new attribute `detailedHourly` to each daily forecast sensor listing hourly forecasts in kWh
- if there is data missing, sensors will still show something but a debug log will output that the sensor is missing data


v4.0.2
- sensor names **have** changed!! this is due to localisation strings of the integration
- decimal precision changed for forecast tomorrow from 0 to 2
- fixed 7th day forecast missing data that was being ignored
- added new sensor `Power Now`
- added new sensor `Power Next 30 Mins`
- added new sensor `Power Next Hour`
- added localisation for all objects in the integration.. thanks to @ViPeR5000 for getting me started on thinking about this (google translate used, if you find anything wrong PR and i can update the translations)

v4.0.1
- rebased from 3.0.55
- keeps the last 730 days (2 years) of forecast data
- some sensors have have had their device_class and native_unit_of_measurement updated to a correct type
- API polling count is read directly from Solcast and is no longer calculated
- no more auto polling.. its now up to every one to create an automation to poll for data when you want. This is due to so many users now only have 10 api calls a day
- striped out saving UTC time changing and keeping solcast data as it is so timezone data can be changed when needed
- history items went missing due to the sensor renamed. no longer using the HA history and instead just storing the data in the solcast.json file
- removed update actual service.. actual data from solcast is no longer polled (it is used on the first install to get past data so the integration works and i don't get issue reports because solcast do not give full day data, only data from when you call)
- lots of the logging messages have been updated to be debug,info,warning or errors
- some sensors **COULD** possibly no longer have extra attribute values or attribute values may have been renamed or have changed to the data stored within
- greater in depth diagnostic data to share when needed to help debug any issues
- some of @rany2 work has been now integrated

Removed 3.1.x
- too many users could not handle the power of this release
- v4.x.x replaces 3.0.55 - 3.1.x with new changes

v3.0.47
- added attribute weekday name for sensor forecasts, today, tomorrow, D3..7
  can read the names via the template 
{{ state_attr('sensor.solcast_forecast_today', 'dayname') }}
{{ state_attr('sensor.solcast_forecast_today', 'dayname') }}
{{ state_attr('sensor.solcast_forecast_tomorrow', 'dayname') }}
{{ state_attr('sensor.solcast_forecast_D3', 'dayname') }}
{{ state_attr('sensor.solcast_forecast_D4', 'dayname') }}
{{ state_attr('sensor.solcast_forecast_D5', 'dayname') }}
{{ state_attr('sensor.solcast_forecast_D6', 'dayname') }}
{{ state_attr('sensor.solcast_forecast_D7', 'dayname') }}

v3.0.46
- possible Maria DB problem - possible fix

v3.0.45
- pre release
- currently being tested 
- wont hurt anything if you do install it

v3.0.44
- pre release
- better diagnostic data
- just for testing
- wont hurt anything if you do install it

v3.0.43
- pre release not for use!!
- do not install :) just for testing

v3.0.42
- fixed using the service to update forecasts from calling twice

v3.0.41
- recoded logging. Re-worded. More debug vs info vs error logging.
- API usage counter was not recorded when reset to zero at UTC midnight
- added a new service where you can call to update the Solcast actual data for the forecasts
- added the version info to the integration UI

v3.0.40
- someone left some unused code in 3.0.39 causing problems

v3.0.39
- removed version info

v3.0.38
- error with v3.0.37 fix for updating sensors

v3.0.37
- make sure the hourly sensors update when auto polling is disabled

v3.0.36
- includes all pre release items
- actual past accurate data is now set to only poll the API at midday and last hour of the day (so only twice a day)

v3.0.35 - PRE RELEASE
- extended the internet connection timeout to 60s

v3.0.34 - PRE RELEASE
- added service to clear old solcast.json file to have a clean start
- return empty energy graph data if there is an error generating info

v3.0.33
- added sensors for forecast days 3,4,5,6,7

v3.0.32
- refactored HA setup function call requirements
- refactored some other code with typos to spell words correctly.. no biggie

v3.0.30
- merged in some work by @696GrocuttT PR into this release
- fixed code to do with using up all allowed api counts
- this release will most likely stuff up the current API counter, but after the UTC counter reset all will be right in the world of api counting again

v3.0.29
- changed Peak Time Today/Tomorrow sensor from datetime to time
- changed back the unit for peak measurement to Wh as the sensor is telling the peak/max hours generated forecast for the hour
- added new configuration option for the integration to disable auto polling. Users can then setup their own automation to poll for data when they like (mostly due to the fact that Solcast have changed the API allowance for new accounts to just 10 per day)
- API counter sensor now shows total used instead of allowance remaining as some have 10 others 50. It will 'Exceeded API Allowance' if you have none left


v3.0.27
- changed unit for peak measurement #86 thanks Ivesvdf
- some other minor text changes for logs
- changed service call thanks 696GrocuttT
- including fix for issue #83

v3.0.26
- testing fix for issue #83

v3.0.25
- removed PR for 3.0.24 - caused errors in the forecast graph
- fixed HA 2022.11 cant add forecast to solar dashboard

v3.0.24
- merged PR from @696GrocuttT 

v3.0.23
- added more debug log code
- added the service to update forecast

v3.0.22
- added more debug log code

v3.0.21
- added more debug logs for greater info

v3.0.19
- FIX: coordinator.py", line 133, in update_forecast for update_callback in self._listeners: RuntimeError: dictionary changed size during iteration
- this version needs HA 2022.7+ now

v3.0.18
- changed api counter return value calculations

v3.0.17
- set the polling api time to 10mins after the hour to give solcast api time to calculate satellite data

v3.0.16
- fixed api polling to get actual data once in a while during the day
- added full path to data file - thanks OmenWild

v3.0.15
- works in both 2022.6 and 2022.7 beta

v3.0.14
- fixes HA 2022.7.0b2 errors (seems to :) )

v3.0.13
- past graphed data did not reset at midnight local time
- missing asyncio import

v3.0.12
- graphed data for week/month/year was not ordered so the graph was messy

v3.0.11
- added timeout for solcast api server connections
- added previous 7 day graph data to the energy dashboard (only works if you are recording data)

v3.0.9
- **users upgrading from v3.0.5 or lover, need to delete the 'solcast.json' file in the HA>config directory to stop any errors**
- renamed sensors with the prefix "solcast_" to help naming sensors easier
- ** you will get double ups of the sensors in the integration because of the naming change. these will show greyed out in the list or with the values like unknown or unavailable etc.. just delete these old sensors one by one from the integration **

v3.0.6
- **users upgrading from v3.0.x need to delete the 'solcast.json' file in the HA>config directory**
- fixed lots of little bugs and problems.
- added ability to add multiple solcast accounts. Just comma separate the api_keys in the integration config.
- remained API Counter to API Left. shows how many is remaining rather than used count.
- 'actual forecast' data is now only called once, the last api call at sunset. OR during integration install first run.
- forecast data is still called every hour between sunrise and sunset and once at midnight every day.
*Just delete the old API Counter sensor as its not used now*

v3.0.5 beta
- fixed 'this hour' amd 'next hour' sensor values.
- slow down the api polling if more than 1 rooftop to poll.
- fix first hour graph plot data.
- possibly RC1?? will see.

v3.0.4 beta
- bug fixes.

v3.0
- complete re write

Earlier history is unavailable.
</details>

## Credits

Modified from the great works of
* oziee/ha-solcast-solar
* @rany2 - ranygh@riseup.net
* dannerph/homeassistant-solcast
* cjtapper/solcast-py
* home-assistant-libs/forecast_solar
