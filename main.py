import streamlit as st
from spider import Spiders
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import re
import io  # 用于处理内存中的文件
plt.rcParams['font.sans-serif']=['SimHei']
sns.set(font_scale=1.5,font='STSong')
font_path = 'SimHei.ttf'
font_prop = FontProperties(fname=font_path, size=14)
# 设置页面
st.set_page_config(page_title="房地产数据爬虫", layout="wide")

# CSS样式
st.markdown("""
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .custom-font {
        font-size:18px;
    }
    .custom-button {
        background-color: #4CAF50;
        color: white;
        padding: 0.25em 0.5em;
        text-align: center;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 界面标题
st.markdown('<p class="big-font">房地产数据爬虫</p>', unsafe_allow_html=True)

# 创建一个爬虫实例
spider = Spiders(url="https://gz.fang.lianjia.com/")

# 侧边栏配置
with st.sidebar:
    st.header('配置')
    spider.get_cityinfo()
    city = st.selectbox('选择城市', list(spider.city_dict.keys()))
    max_pages = 200  # 默认的最大页数
    if city:
        spider.city_url = spider.city_dict[city]
        spider.city_name = city
        max_pages = spider.get_maxpagenum()  # 获取并显示选定城市的最大页数
        if max_pages == 'error':
            st.error('无法获取该城市的最大页数。')
            max_pages = 200
        else:
            st.write(f'该城市共有 {max_pages} 页数据可供爬取。')

    # 确定爬取页数
    pages_choice = st.number_input('选择要爬取的页数', min_value=1,
                                   max_value=max_pages if max_pages != 'error' else 100, step=1)

# 主界面
col1, col2 = st.columns(2)
with col1:
    st.markdown('<p class="custom-font">请选择城市和爬取页数，然后点击下方按钮开始爬取数据。</p>', unsafe_allow_html=True)

# 在Streamlit中显示DataFrame和下载按钮
if st.button('爬取数据', key="fetch_data"):
    with st.spinner('正在爬取数据...'):
        spider.get_citydata(pages_choice)
        if spider.data_list:
            st.success('数据爬取完成')
            df = pd.DataFrame(spider.data_list)
            st.dataframe(df)

            # 创建三列布局
            col1, col2, col3 = st.columns(3)

            # CSV下载
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(label="下载数据为CSV", data=csv, file_name='data.csv', mime='text/csv')

            # JSON下载
            with col2:
                # 确保在转换为JSON之前设置了 ensure_ascii=False
                json_data = df.to_json(orient='records', force_ascii=False, lines=True)
                st.download_button(
                    label="下载数据为JSON",
                    data=json_data.encode('utf-8'),  # 编码为utf-8
                    file_name='data.json',
                    mime='application/json'
                )

            # Excel下载
            with col3:
                to_write = io.BytesIO()
                df.to_excel(to_write, index=False, engine='openpyxl')  # 写入到BytesIO对象
                to_write.seek(0)  # 移动到文件开始位置
                st.download_button(label="下载数据为Excel", data=to_write, file_name='data.xlsx',
                                   mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


            # 数据清洗函数

            # 清洗 '均价' 列的函数

        else:
            st.error('未能获取数据')
    df = pd.DataFrame(spider.data_list)

    # 清洗 '均价' 列的函数
    def extract_number(text):
        match = re.search(r'(\d+)', text)
        return int(match.group()) if match else None

    # 清洗数据
    if 'df' in locals() and not df.empty:
        # 清洗 '均价' 列的函数
        def extract_number(text):
            match = re.search(r'(\d+)', text)
            return int(match.group()) if match else None


        # 清洗数据
        df['均价数值'] = df['均价'].apply(extract_number)

        # 基本统计分析
        average_price = df['均价数值'].mean()
        median_price = df['均价数值'].median()
        st.write(f'均价的平均值是：{average_price}元/㎡')
        st.write(f'均价的中位数是：{median_price}元/㎡')

        # 可视化 - 均价分布情况
        try:
            fig, ax = plt.subplots()
            sns.histplot(df['均价数值'].dropna(), kde=False, ax=ax)
            ax.set_title('均价分布情况',fontproperties=font_prop)
            ax.set_xlabel('价格 (元/㎡)',fontproperties=font_prop)
            ax.set_ylabel('频数',fontproperties=font_prop)
            st.pyplot(fig)
        except Exception as e:
            st.error(f"绘图时发生错误：{e}")



