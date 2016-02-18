import re
import sys
import dateutil
import pandas as pd
import matplotlib.pyplot as plt


date_patterns = {
"long_datetime" : "(?P<datetime>\d{1,2}\s{1}\w{3}(\s{1}|\s{1}\d{4}\s{1})\d{2}:\d{2})",
"short_datetime" : "(?P<datetime>\d{2}/\d{2}/\d{4},\s{1}\d{2}:\d{2})"
}

message_pattern = "\s{1}-\s{1}(?P<name>(.*?)):\s{1}(?P<message>(.*?))$"
action_pattern = "\s{1}-\s{1}(?P<action>(.*?))$"

action_strings = {
"admin": "admin",
"change_icon": "changed this group's icon",
"change_subject": "changed the subject",
"added": "added",
"left": "left",
"removed": "removed"
}


class ChatElement:
    def __init__(self, datetime, name, message, action):
        self.datetime = datetime
        self.name = name
        self.message = message
        self.action = action


class Chat:
    def __init__(self, filename):
        self.filename = filename

    def open_file(self):
        x = open(self.filename,'r')
        y = x.read()
        content = y.splitlines()
        return content

class Parser:
    def parse_message(self,str):
        for pattern in map(lambda x:x+message_pattern, date_patterns.values()):
            m = re.match(pattern, str)
            if m:
                return (m.group('datetime'), m.group('name'), m.group('message'), None)

        # if code comes here, message is continuation or action
        for pattern in map(lambda x:x+action_pattern, date_patterns.values()):
            m = re.match(pattern, str)
            if m:
                if any(action_string in m.group('action') for action_string in action_strings.values()):
                    for pattern in map(lambda x: "(?P<name>(.*?))"+x+"(.*?)", action_strings.values()):
                        m_action = re.match(pattern, m.group('action'))
                        if m_action:
                            return (m.group('datetime'), m_action.group('name'), None, m.group('action'))

                    sys.stderr.write("[failed to capture name from action] - %s\n" %(m.group('action')))
                    return (m.group('datetime'), None, None, m.group('action'))

        #prone to return invalid continuation if above filtering doesn't cover all patterns for messages and actions
        return (None, None, str, None)

    def process(self, content):
        messages = []
        for row in content:
            parsed = self.parse_message(row)
            if parsed[0] is None:
                messages[-1].message += parsed[2]
            else:
                messages.append(ChatElement(*parsed))
        j = 1
        df = pd.DataFrame(index=range(1, len(messages)+1), columns=['name','message','action','date_string'])
        for message in messages:
            if message.datetime is None:
                sys.stderr.write("[failed to add chatelement to dataframe] - %s, %s, %s, %s\n" %(message.datetime, message.name, message.message, message.action))
            else:
                df.ix[j]['name'] = message.name
                df.ix[j]['message'] = message.message
                df.ix[j]['action'] = message.action
                df.ix[j]['date_string'] = message.datetime
            j += 1

        df['Time'] = df['date_string'].map(lambda x: dateutil.parser.parse(x))
        df['Day'] = df['date_string'].map(lambda x: dateutil.parser.parse(x).strftime("%a"))
        df['Date'] = df['date_string'].map(lambda x:dateutil.parser.parse(x).strftime("%x"))
        df['Hour'] = df['date_string'].map(lambda x:dateutil.parser.parse(x).strftime("%H"))

        df_actions = df[pd.isnull(df['message'])]
        df_messages = df[pd.isnull(df['action'])]

        return df_messages, df_actions


#def responses(df):
#    ## Create Empty Response Matrix
#    labels = df['name'].unique()
#    responses = pd.DataFrame(0,index=labels,columns=labels)
#
#    ## Update values in Response Matrix
#    # self.df.sort(columns='Time', inplace = 1)
#    x, y = 1, 2
#    while y < len(df):
#        n1 = df.ix[x]['name']
#        n2 = df.ix[y]['name']
#        if n1 != n2: #only responses to others are valid
#            responses.loc[n1,n2]=responses.loc[n1,n2]+1
#        y = y + 1
#        x = x + 1
#    return responses


def charts(df):
    ## Create Canvas
    fig = plt.figure()
    plt.title = "Whatsappening"
    ax1 = plt.subplot2grid((4,6), (0,0), rowspan=2, colspan=2)
    ax2 = plt.subplot2grid((4,6), (0,2),rowspan=2,colspan=2)
    ax3 = plt.subplot2grid((4,6),(0,4), rowspan=2, colspan=2)
    ax4 = plt.subplot2grid((4,6),(2,0), rowspan=2, colspan = 6)


    ## Create Charts
    df.groupby('Hour').count().plot(ax=ax1, legend = None, title ="Hour of Day")
    df.groupby('Day').count().plot(y="message",ax=ax2, kind='bar', legend = None, title = 'Days')
    df.name.value_counts().plot(ax=ax3,kind = 'bar', title = 'Number of messages')
    df.groupby('Date').count().plot(y="message",ax=ax4, legend = None, title = 'Message by Date')
    plt.subplots_adjust(wspace=0.46, hspace=1)
    plt.show()

def main():
    chat1 = Chat("chat1.txt")
    chat2 = Chat("chat2.txt")
    content = chat1.open_file() + chat2.open_file()
    parser = Parser()
    df_messages, df_actions = parser.process(content)
    print charts(df_messages)


if __name__ == '__main__':
    main()
