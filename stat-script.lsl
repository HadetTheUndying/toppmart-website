key http_request_id;

string ip = "toppmart.org";
string base_url = "";
string secret = "CHANGE ME";
 
integer elapsed = 0;
 
get(string path, string args)
{
    integer i;
    string body = "";
    http_request_id = llHTTPRequest(base_url + path + args,[HTTP_METHOD,"GET",HTTP_MIMETYPE,"application/x-www-form-urlencoded"],body);
}

post(string path, list args)
{
    integer i;
    string body;
    integer len=llGetListLength(args) & 0xFFFE; // make it even
    for (i=0;i<len;i+=2)
    {
        string varname=llList2String(args,i);
        string varvalue=llList2String(args,i + 1);
        if (i>0) body+="&";
        body+=llEscapeURL(varname)+"="+llEscapeURL(varvalue);
    }
    http_request_id = llHTTPRequest(base_url + path,[HTTP_METHOD,"POST",HTTP_MIMETYPE,"application/x-www-form-urlencoded", HTTP_VERIFY_CERT, FALSE],body);
}

list last_agents = [];

float delay = 5.0;

dump() 
{
    list agents = llGetAgentList(AGENT_LIST_REGION, []);
    integer length = llGetListLength(agents);
    string output = "";
    integer i = 0;
    if(length > 0) {
        for(i = 0; i < length; i++) {
            key k = llList2Key(agents, i);
            if(i > 0) {
                output += ":";
            }
            vector pos = llList2Vector(llGetObjectDetails(k, [OBJECT_POS]), 0);
            output += llKey2Name(k) + "," + (string)pos.x + "," + (string)pos.y;
        }
       post("dump/" + secret, ["players", output]);
    }
}

default
{
    touch_start(integer num_detected) {
        llLoadURL(llDetectedKey(0), "Visit the Official Toppmart Website!", "https://" + ip);    
    }

    state_entry()
    {
        base_url = "http://" + ip + "/sim/";
        llSetText("Touch to visit the official ToppMart webpage!", <1,1,1>, 1);
        llListen(PUBLIC_CHANNEL, "", "", "");
        get("reset/" + secret, "");
        llSetTimerEvent(delay);
    }

    timer()
    {
        dump();
    }
}