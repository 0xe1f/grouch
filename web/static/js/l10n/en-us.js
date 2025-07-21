/*****************************************************************************
 ** Copyright (C) 2024 Akop Karapetyan
 **
 ** Licensed under the Apache License, Version 2.0 (the "License");
 ** you may not use this file except in compliance with the License.
 ** You may obtain a copy of the License at
 **
 **     http://www.apache.org/licenses/LICENSE-2.0
 **
 ** Unless required by applicable law or agreed to in writing, software
 ** distributed under the License is distributed on an "AS IS" BASIS,
 ** WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 ** See the License for the specific language governing permissions and
 ** limitations under the License.
 ******************************************************************************
 */

var dateTimeFormatter = function(date, sameDay) {
    if (sameDay) {
        // Return time string (e.g. "10:30 AM")
        var hours = date.getHours();
        var ampm = (hours < 12) ? "AM" : "PM";
        var twelveHourHours = hours;

        if (hours == 0) {
            twelveHourHours = 12;
        } else if (hours > 12) {
            twelveHourHours -= 12;
        }

        var minutes = date.getMinutes() + "";
        if (minutes.length < 2) {
            minutes = "0" + minutes;
        }

        return twelveHourHours + ":" + minutes + " " + ampm;
    } else {
        // Return date string (e.g. "Jan 5, 2010")
        var months = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" ];
        return months[date.getMonth()] + " " + date.getDate() + ", " + date.getFullYear();
    }
};
