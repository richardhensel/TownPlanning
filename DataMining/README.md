# DataMining

TODO:

create a 'processed data' table and a 'raw data' table
How far back to go? database each line, each name/value? each field just without tests for regular expressions?

get latitude and longitude of each rp

remove duplicate entries for aspects or descriptions. 

add lot numbers to the rp table.

put all of the expected values into their own class with a set of 'test string' fragments and a 'proper name' which is actually databased



DONE: 

now concatenate the information from multiple lines with the same title.

rp table tests for RP type and number

fix area to remove m2 and any other characters added in error. 

address and rp are now databased. 

fix issue extracting the rp number with integers being wrongly included. 

add test for each zone from list of possible outcomes. 

add test for each aspect of development from list of possible outcomes. 

sometimes multiple names of ward - fix this

aspects of development may be included under the same or different headings. extract these into their own table

get accurate count of number of rps, number of aspects and number of descriptions

populate the number of units column. 

put the xml reader into its own class.

add utc time for submission dates

tidy up the destinction betwen numeric and alphabetically spelled stage numbers
