###############################################################################
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
###############################################################################

import pytest
import logging
from synop2bufr import extract_individual_synop, parse_synop, transform

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def multiple_reports_307080():
    return """AAXX 21120
15015 02999 02501 10103 21090 39765 42952 57020 60001=
15020 02997 23104 10130 21075 30177 40377 58020 60001 81041=
15090 02997 53102 10139 21075 30271 40364 58031 60001 82046=
    """


@pytest.fixture
def multiple_reports_307096():
    return """AAXX 21121
15015 02999 02501 10103 21090 39765 42952 57020 60001=
15020 02997 23104 10130 21075 30177 40377 58020 60001 81041=
15090 02997 53102 10139 21075 30271 40364 58031 60001 82046=
    """


@pytest.fixture
def single_report():
    return """AAXX 21121
15001 05515 32931 10103 21090 39765 42250 57020 60071 72006 82110 91155
 333 10178 21073 34101 55055 00010 20003 30002 50001 60004
 60035 70500 83145 81533 91008 91111
 444 18031 22053
    """


@pytest.fixture
def metadata_string():
    md = "station_name,wigos_station_identifier,traditional_station_identifier,facility_type,latitude,longitude,elevation,barometer_height,territory_name,wmo_region\n" + \
            "OCNA SUGATAG,0-20000-0-15015,15015,Land (fixed),47.77706163,23.94046026,503,504.43,Romania,6\n" + \
            "BOTOSANI,0-20000-0-15020,15020,Land (fixed),47.73565324,26.64555017,161,162.2,Romania,6\n" + \
            "IASI,0-20000-0-15090,15090,Land (fixed),47.16333333,27.62722222,74.29,75.69,Romania,6"  # noqa
    return md


def test_report_separation(multiple_reports_307080):
    # Extract each report
    msg_list = extract_individual_synop(multiple_reports_307080)
    assert len(msg_list) == 3
    # Assert each report has been extracted as intended
    assert msg_list[0] == "AAXX 21120 15015 02999 02501 10103 21090 39765 42952 57020 60001"  # noqa
    assert msg_list[1] == "AAXX 21120 15020 02997 23104 10130 21075 30177 40377 58020 60001 81041"  # noqa
    assert msg_list[2] == "AAXX 21120 15090 02997 53102 10139 21075 30271 40364 58031 60001 82046"  # noqa


def test_conversion(single_report):
    # Get the returned dictionary from the report, using a random
    # year and month
    d, num_s3_clouds, num_s4_clouds = parse_synop(single_report, 2000, 1)
    # We now need to check that most the dictionary items are what we expect
    assert d['station_id'] == "15001"
    assert d['day'] == 21
    assert d['hour'] == 11
    assert d['minute'] == 55
    assert d['WMO_station_type'] == 0
    assert d['lowest_cloud_base'] == 600
    assert d['visibility'] == 1500
    assert d['cloud_cover'] == 38
    assert d['wind_direction'] == 290
    assert d['wind_speed'] == 31
    assert d['air_temperature'] == 283.45
    assert d['dewpoint_temperature'] == 264.15
    assert d['station_pressure'] == 97650
    assert d['isobaric_surface'] == 92500
    assert d['geopotential_height'] == 1250
    assert d['pressure_tendency_characteristic'] == 7
    assert d['3hr_pressure_change'] == -200
    assert d['precipitation_s1'] == 7
    assert d['ps1_time_period'] == -6
    assert d['present_weather'] == 20
    assert d['past_weather_1'] == 0
    assert d['past_weather_2'] == 6
    assert d['cloud_amount_s1'] == 2
    assert d['low_cloud_type'] == 31
    assert d['middle_cloud_type'] == 21
    assert d['high_cloud_type'] == 10
    assert d['maximum_temperature'] == 290.95
    assert d['minimum_temperature'] == 265.85
    assert d['maximum_temperature_period_start'] == -12
    assert d['maximum_temperature_period_end'] == 0
    assert d['minimum_temperature_period_start'] == -12
    assert d['minimum_temperature_period_end'] == 0
    assert d['ground_state'] == 4
    assert d['ground_temperature'] == 272.15
    assert d['sunshine_amount_24hr'] == 330
    assert d['net_radiation_24hr'] == 100000
    assert d['global_solar_radiation_24hr'] == 30000
    assert d['diffuse_solar_radiation_24hr'] == 20000
    assert d['long_wave_radiation_24hr'] == -10000
    assert d['short_wave_radiation_24hr'] == 40000
    assert d['precipitation_s3'] == 3
    assert d['ps3_time_period'] == -1
    assert d['precipitation_24h'] == 50
    assert d['cloud_amount_s3_1'] == 3
    assert d['cloud_genus_s3_1'] == 1
    assert d['cloud_height_s3_1'] == 1350
    assert d['cloud_amount_s3_2'] == 1
    assert d['cloud_genus_s3_2'] == 5
    assert d['cloud_height_s3_2'] == 990
    assert d['highest_gust_1'] == 8
    assert d['highest_gust_2'] == 11
    assert d['cloud_amount_s4_1'] == 1
    assert d['cloud_genus_s4_1'] == 8
    assert d['cloud_height_s4_1'] == 300
    assert d['cloud_top_s4_1'] == 1
    assert d['cloud_amount_s4_2'] == 2
    assert d['cloud_genus_s4_2'] == 2
    assert d['cloud_height_s4_2'] == 500
    assert d['cloud_top_s4_2'] == 3
    assert num_s3_clouds == 2
    assert num_s4_clouds == 2


def test_bufr_307080(multiple_reports_307080, metadata_string):
    result = transform(
        multiple_reports_307080, metadata_string, 2022, 3
    )
    msgs = {}
    for item in result:
        msgs[item['_meta']['id']] = item
    # Test the md5 keys
    assert msgs['WIGOS_0-20000-0-15015_20220321T120000']['_meta']['properties']['md5'] == '603e1c2c25591a8d4213f339a1ce3b52'  # noqa
    assert msgs['WIGOS_0-20000-0-15020_20220321T120000']['_meta']['properties']['md5'] == '320ad7f1c3f7940a3059ca04dbb6d74a'  # noqa
    assert msgs['WIGOS_0-20000-0-15090_20220321T120000']['_meta']['properties']['md5'] == '3215ebdc66707c46458d2bbacb49427e'  # noqa

    # Test the bufr template used for all the reports
    # (they should be the same for every report)
    assert msgs['WIGOS_0-20000-0-15015_20220321T120000']['_meta']['template'] == 307080  # noqa
    assert msgs['WIGOS_0-20000-0-15020_20220321T120000']['_meta']['template'] == 307080  # noqa
    assert msgs['WIGOS_0-20000-0-15090_20220321T120000']['_meta']['template'] == 307080  # noqa


def test_bufr_307096(multiple_reports_307096, metadata_string):
    result = transform(
        multiple_reports_307096, metadata_string, 2022, 3
    )
    msgs = {}
    for item in result:
        msgs[item['_meta']['id']] = item
    # Test the md5 keys
    assert msgs['WIGOS_0-20000-0-15015_20220321T120000']['_meta']['properties']['md5'] == '27c990045879acc2eedddb7fdc70db4d'  # noqa
    assert msgs['WIGOS_0-20000-0-15020_20220321T120000']['_meta']['properties']['md5'] == '9db622c40d53aae4ce4f38a658f36d86'  # noqa
    assert msgs['WIGOS_0-20000-0-15090_20220321T120000']['_meta']['properties']['md5'] == '89f424b9fc38a6db69c7b195bd71d92f'  # noqa

    # Test the bufr template used for all the reports
    # (they should be the same for every report)
    assert msgs['WIGOS_0-20000-0-15015_20220321T120000']['_meta']['template'] == 307096  # noqa
    assert msgs['WIGOS_0-20000-0-15020_20220321T120000']['_meta']['template'] == 307096  # noqa
    assert msgs['WIGOS_0-20000-0-15090_20220321T120000']['_meta']['template'] == 307096  # noqa


def test_invalid_separation():

    missing_delimiter = """AAXX 21121

15015 02999 02501 10103 21090 39765 42952 57020 60001

15020 02997 23104 10130 21075 30177 40377 58020 60001 81041

15090 02997 53102 10139 21075 30271 40364 58031 60001 82046"""

    with pytest.raises(Exception) as e:
        # Attempt to extract each report
        extract_individual_synop(missing_delimiter)
        assert str(
            e.value) == (
                        "Delimiters (=) are not present in the string,"
                        " thus unable to identify separate SYNOP reports."
                        )  # noqa


def test_no_type():

    missing_station_type = """21121
           15001 05515 32931 10103 21090
    39765 42250 57020 60071 72006 82110 91155="""

    with pytest.raises(Exception) as e:
        # Attempt to decode the report
        extract_individual_synop(
            missing_station_type)
        assert str(
            e.value) == "Invalid SYNOP message: AAXX could not be found."


def test_no_time():

    missing_time = """AAXX
           15001 05515 32931 10103 21090
    39765 42250 57020 60071 72006 82110 91155"""

    with pytest.raises(Exception) as e:
        # Attempt to decode the message
        parse_synop(missing_time)
        assert str(
            e.value) == ("No SYNOP reports were extracted."
                         " Perhaps the date group YYGGiw"
                         " is missing.")


def test_no_tsi():

    missing_tsi = """AAXX 21121
           05515 32931 10103 21090
    39765 42250 57020 60071 72006 82110 91155="""

    with pytest.raises(Exception) as e:
        # Attempt to decode the message
        parse_synop(missing_tsi)
        assert str(
            e.value) == ("Unexpected precipitation group"
                         " found in section 1, thus unable to"
                         " decode. Section 0 groups may be"
                         " missing.")
