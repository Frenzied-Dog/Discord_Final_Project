import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests,bs4,matplotlib
import io
matplotlib.use('agg')

rate_url = "https://rate.bot.com.tw/xrt/quote/l6m/%s"
currency_choice = ["USD","EUR","CNY","JPY","HKD","GBP","AUD","SGD"]
en2cn_dict = {"Cash_BID": "現金買入", "Cash_ASK": "現金賣出", "IMM_BID": "即期買入", "IMM_ASK": "即期賣出"}


def get_info(currency: str) -> pd.DataFrame:
    try:
        htmlfile = requests.get(f"https://rate.bot.com.tw/xrt/quote/l6m/{currency}")
    except Exception as err:
        print(f"網頁下載失敗: {err}")

    soup = bs4.BeautifulSoup(htmlfile.text,'lxml')

    tbody = soup.find('tbody')
    all_rates_rows = tbody.find_all('tr')

    ret = []
    for item in all_rates_rows:
        onerow = []
        onerow.append(item.find("td", class_="text-center").find("a").getText()[2:])
        
        item0 = item.find_all("td", class_="rate-content-cash text-right print_table-cell")
        for i in item0: onerow.append(i.getText())
        
        item1=item.find_all("td", class_="rate-content-sight text-right print_table-cell")
        for i in item1: onerow.append(i.getText())
        ret.append(onerow)

    
    df = pd.DataFrame(ret, columns=["Date", "Cash_BID", "Cash_ASK", "IMM_BID", "IMM_ASK"])
    df.set_index("Date", inplace=True)
    df = df.astype(float)
    print(f"{currency}分析網頁、整理資訊成功")
    return df


def find_updown(main_datas: dict, cur: str) -> dict[str, pd.DataFrame]:
    data: pd.DataFrame = main_datas[cur]["raw_data"]
    
    updowndata: list[list[str | float]] = []
    counts: pd.DataFrame = pd.DataFrame([[0 for _ in range(4)] for _ in range(3)],
                                       columns=data.columns, index=["increase","decrease","unchanged"])
    
    for i in range(0,len(data)-1):
        updowndata.append(["%s~%s" % (data.index[i+1], data.index[i])])
        for j in data.columns:
            num = data[j].iloc[i] - data[j].iloc[i+1]
            updowndata[-1].append(num)
            
            if num > 0: counts.at["increase", j] += 1
            elif num < 0: counts.at["decrease", j] += 1
            else: counts.at["unchanged", j] += 1

    df = pd.DataFrame(updowndata, columns=["Date"] + list(data.columns))
    df.set_index("Date", inplace=True)

    return {"raw": df, "counts": counts}


def analyze(main_datas: dict, cur: str) -> pd.DataFrame:
    data: pd.DataFrame = main_datas[cur]["raw_data"]
    df_list: list[list[str | float]] = []
    
    for i in data.columns:
        df_list.append([data[i].max(), data[i].idxmax(), data[i].min(), data[i].idxmin(), data[i].mean()])
    
    df = pd.DataFrame(df_list, columns=["Max", "Max_Date", "Min", "Min_Date", "Mean"], index=data.columns)

    return df


def find_change(main_datas: dict, cur: str) -> dict[str, pd.DataFrame]:
    data: pd.DataFrame = main_datas[cur]["raw_data"]
    change: list[list[str | float]] = []
    
    for i in range(0,len(data)-1):
        for j in range(i+1,len(data)):
            change.append(["%s~%s" % (data.index[j], data.index[i]), #換成外幣日期、換回台幣日期
                           data['Cash_BID'].iloc[i] - data['Cash_ASK'].iloc[j], #現金匯率差
                           data['IMM_BID'].iloc[i] - data['IMM_ASK'].iloc[j]]) #即期匯率差
    
    result: list[list[str | float]] = []
    result.append(max(change, key=lambda x: x[1])[:2])
    result.append(min(change, key=lambda x: x[1])[:2])
    result.append(max(change, key=lambda x: x[2])[::2])
    result.append(min(change, key=lambda x: x[2])[::2])
    result_df = pd.DataFrame(result, columns=["Date_Interval", "Change"], index=["Cash_Best", "Cash_Worst", "Spot_Best", "Spot_Worst"])
    
    raw_df = pd.DataFrame(change, columns=["Date_Interval", "Cash_Change", "Spot_Change"])
    raw_df.set_index("Date_Interval", inplace=True)
    return {"raw": raw_df, "result": result_df}


def get_BID_ASK_chart(main_datas: dict, cur: str) -> io.BytesIO:
    main_datas[cur]["raw_data"].iloc[::-1].plot(style='-o', figsize=(12,9), fontsize=8, grid=True, sharex=False,
                                                subplots=[("Cash_BID", "Cash_ASK"), ("IMM_BID", "IMM_ASK")],
                                                xlabel="Time", ylabel="Rate", title=f"{cur} Cash BID vs ASK")

    data_stream = io.BytesIO()
    plt.savefig(data_stream, format="png", bbox_inches="tight")
    data_stream.seek(0)
    plt.close()
    return data_stream


def get_predict(main_datas: dict, power_num: list[int], cur: str) -> io.BytesIO:
    #把時間軸轉換成均勻的時間軸
    y: pd.Series = main_datas[cur]["raw_data"]["Cash_BID"].loc[::-1].to_numpy()
    x = np.linspace(0, 0.5, len(y))
    
    m1 = np.poly1d(np.polyfit(x,y,power_num[0]))
    m2 = np.poly1d(np.polyfit(x,y,power_num[1]))
    m3 = np.poly1d(np.polyfit(x,y,power_num[2]))
    t1 = f"{cur} degree = {power_num[0]}"
    t2 = f"{cur} degree = {power_num[1]}"
    t3 = f"{cur} degree = {power_num[2]}"

    plt.figure(figsize=(12,9))
    
    plt.subplot(2,1,1)
    plt.title(cur+" Model")
    plt.xlabel("Time")
    plt.ylabel("Rate")
    plt.scatter(x,y)
    plt.plot(x,m1(x),label=t1)
    plt.plot(x,m2(x),label=t2)
    plt.plot(x,m3(x),label=t3)
    plt.legend()

    predict_y1: np.ndarray = y.copy()
    predict_y2: np.ndarray = y.copy()
    predict_y3: np.ndarray = y.copy()
    
    for i in range(1,11):
        predict_y1 = np.append(predict_y1, [m1(0.5+0.5/128*i)])
        predict_y2 = np.append(predict_y2, [m2(0.5+0.5/128*i)])
        predict_y3 = np.append(predict_y3, [m3(0.5+0.5/128*i)])
    px = np.linspace(0, 0.5+0.5/128*30, len(y)+10)

    pm1 = np.poly1d(np.polyfit(px,predict_y1,power_num[0]))
    pm2 = np.poly1d(np.polyfit(px,predict_y2,power_num[1]))
    pm3 = np.poly1d(np.polyfit(px,predict_y3,power_num[2]))
    
    plt.subplot(2,1,2)
    plt.title(cur+" Prediction")
    plt.xlabel("Time")
    plt.ylabel("Rate")
    t1 = f"{cur} degree = {power_num[0]}"
    t2 = f"{cur} degree = {power_num[1]}"
    t3 = f"{cur} degree = {power_num[2]}"

    plt.scatter(px,predict_y1)
    plt.plot(px,pm1(px),label=t1)
    plt.scatter(px,predict_y2)
    plt.plot(px,pm2(px),label=t2)
    plt.scatter(px,predict_y3) 
    plt.plot(px,pm3(px),label=t3)
    plt.legend()
    plt.subplots_adjust(hspace=0.5)
    
    # plt.show()
    data_stream = io.BytesIO()
    plt.savefig(data_stream, format="png", bbox_inches="tight")
    data_stream.seek(0)
    plt.close()
    return data_stream


def get_compare_bar_chart(main_datas: dict, curA: str, curB: str) -> io.BytesIO:
    dataA = main_datas[curA]["updown"]["raw"]
    dataB = main_datas[curB]["updown"]["raw"]
    
    compared_data = pd.concat([dataA["Cash_BID"], dataB["Cash_BID"]], axis=1)
    compared_data.columns = [curA+"_Cash_BID", curB+"_Cash_BID"]
    compared_data.index = ["20"+i[-8:] for i in compared_data.index]
    
    compared_data.loc[::-1].plot.bar(figsize=(12,9), fontsize=6, sharex=False, legend=[curA, curB],
                       xlabel="Time", ylabel="Rate", title=f"{curA} vs {curB} Cash_BID")
    # plt.show()
    data_stream = io.BytesIO()
    plt.savefig(data_stream, format="png", bbox_inches="tight")
    data_stream.seek(0)
    return data_stream


def get_proportion_pie(main_datas: dict, cur: str) -> io.BytesIO:
    data = main_datas[cur]["updown"]["counts"]
    data.plot.pie(y="Cash_BID", ylabel="", legend=False, autopct="%1.2f%%", title=f"{cur} Proportion")
    # plt.show()
    data_stream = io.BytesIO()
    plt.savefig(data_stream, format="png", bbox_inches="tight")
    data_stream.seek(0)
    plt.close()
    return data_stream


if __name__ == "__main__":
    
    datas: dict[str, dict[str, pd.DataFrame | dict[str, pd.DataFrame]]] = {}

    for i in currency_choice: datas[i] = {}
    # for i in currency_choice:
    #     get_info(i)
    #     find_updown(stock[i]["raw_data"], i)
    get_info("USD")
    get_info("AUD")
    find_updown(datas["USD"]["raw_data"], "USD")
    find_updown(datas["AUD"]["raw_data"], "AUD")

    while True:
        print("\n1. 半年內匯率分析\n" +
              "2. 半年內最佳買賣點&日期\n" +
              "3. (現金/即期)買入vs賣出散佈圖\n" +
              "4. 買入匯率預測\n" +
              "5. 兩貨幣買入漲跌關聯長條圖\n" +
              "6. 現金買入漲跌比例圓餅圖\n" +
              "7. 離開程式")
        option = int(input("請選擇功能(目前資料皆為USD,關聯則為USD/AUD): "))
        print()
        
        match option:
            case 1:
                analyze(datas, "USD")
            case 2:
                find_change(datas, "USD")
            case 3:
                get_BID_ASK_chart(datas, "USD")
            case 4:
                get_predict(datas, [4,7,8], "USD")
            case 5:
                get_compare_bar_chart(datas, "USD", "AUD")
            case 6:
                get_proportion_pie(datas, "USD")
            case 7:
                break

        
