import json
rows=[{"kind":"group","text":"Ritu Ahuja 1995 Trust"}]
data=[
("WALMART INC CMN","$50,001-$100,000"),
("WALT DISNEY COMPANY (THE) CMN","$100,001-$250,000"),
("WASHINGTON CNTY WIS GO 2% 03/01/20 MS GO REF BDS UT BNE QUAL BEO","$15,001-$50,000"),
("WASHINGTON ST DB DE GO 01/01/38 FA MOTOR VEHLE FUEL TAX GO BDS 2018D PREM 08/01/29 UT BEO","None"),
("WASTE MANAGEMENT INC CMN","$1,001-$15,000"),
("WATERS CORPORATION COMMON STOCK","None"),
("WAYFAIR INC. CMN","$1,001-$15,000"),
("WEC ENERGY GROUP, INC. CMN","$1,001-$15,000"),
("WELLCARE HEALTH PLANS INC CMN","$1,001-$15,000"),
("WELLS FARGO & CO (NEW) CMN","$50,001-$100,000"),
("WELLTOWER INC. CMN","None"),
("WESTERN ALLIANCE BANCORP CMN","$1,001-$15,000"),
("WESTERN DIGITAL CORPORATION CMN","None"),
("WESTINGHOUSE AIR BRAKE TECHNOL CMN","$15,001-$50,000"),
("WESTLAKE CHEMICAL CORPORATION CMN","$1,001-$15,000"),
("WESTROCK COMPANY CMN","$1,001-$15,000"),
("WEX INC. CMN","None"),
("WEYERHAEUSER COMPANY CMN","$1,001-$15,000"),
("WEYMOUTH MASS GO 1.750X05 04/27/20 FA GO BANS LT BEO","$15,001-$50,000"),
("WHIRLPOOL CORP. CMN","$1,001-$15,000"),
("WHITING PETROLEUM CORPORATION CMN","None"),
("WILLIS TOWERS WATSON PLC CMN","$15,001-$50,000"),
("WORKDAY, INC. CMN CLASS A","$1-$1,000"),
("WORLD WRESTLING ENTERTAINMENT CMN CLASS A","$1,001-$15,000"),
("WORLDPAY INC CMN","None"),
("WPX ENERGY, INC. CMN","$100,001-$250,000"),
("WYANDOTTE CNTY KANS UNI SCH GO 5.250X05 09/01/30 MS DIST NO 500 3PDG UT BDS BEO SR LIEN","$15,001-$50,000"),
("WYNDHAM DESTINATIONS, INC. CMN","None"),
("WYNN RESORTS, LIMITED CMN","$1,001-$15,000"),
("XCEL ENERGY INC. CMN","$1,001-$15,000"),
("XEROX CORPORATION CMN","None"),
("XEROX HOLDINGS CORP CMN","$1,001-$15,000"),
("XILINX INCORPORATED CMN","$1,001-$15,000"),
("YANDEX N.V. CMN","$1,001-$15,000"),
("YUM BRANDS, INC. CMN","$1,001-$15,000"),
("YUM CHINA HOLDINGS, INC. CMN","$1,001-$15,000"),
("ZENDESK, INC. CMN","None"),
("ZILLOW GROUP INC. CMN CLASS A","None"),
("ZILLOW GROUP, INC. CMN SERIES C","$1,001-$15,000"),
("ZIMMER BIOMET HOLDINGS INC","$1,001-$15,000"),
("ZIONS BANCORP CMN","None"),
("ZOETIS INC. CMN CLASS A","$15,001-$50,000"),
]
for nm,val in data:
    rows.append({"kind":"asset","owner":"SP","asset_name":nm,"ticker":None,"eif":None,
        "value":val,"income_types":None,"other_income_spec":None,"amount_of_income":None,"transaction":None})
obj={"pdf_page":39,"printed_label":"Rohit Khanna 39 of 210",
"section":"Schedule A: Assets and Unearned Income","page_type":"schedule_a","filer":"Rohit Khanna",
"layout_note":"Wide value-matrix page (same layout as 037/038); end of the 'Ritu Ahuja 1995 Trust' equity list (W through Z, ending ZOETIS). Single Value block across 12 bucket columns; no Type/Amount-of-Income columns. All owners SP. Value X-columns pixel-detected against the header grid.",
"rows":rows,"free_text":None,
"uncertainties":[
{"row":"muni_bonds","field":"asset_name","read":"long muni descriptions (rows 3,4,19,27)","note":"low-resolution; coupon/date/CUSIP tokens best-effort"}
],
"page_confidence":"medium"}
json.dump(obj,open('docs/2019-2/text/page-039.json','w'),indent=1,ensure_ascii=False)
print("wrote 039:",len(rows),"rows")
