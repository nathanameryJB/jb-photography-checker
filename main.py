import streamlit as st
import pandas as pd
import requests
import base64

st.set_page_config(layout="wide")


def check_image_status(url):
    """Return the status of the image URL. If it's valid (does not return a 4xx or 5xx status code), return True and status code. Otherwise, return False and the status code."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
    }
    try:
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=5)
        if 400 <= response.status_code <= 599:
            return False, response.status_code
        return True, response.status_code
    except requests.RequestException:
        return False, None

def get_table_download_link(df, filename='data.csv'):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
    return href

def display_product_card(product_row, batch_option):
    sku, product_name = product_row['SKU'], product_row['Product Name']
    st.markdown(f"## {sku}", unsafe_allow_html=True)
    st.markdown(f"{product_name}")

    for idx in range(1, 6):
        img_col_name = f"Image {idx}"

        if pd.notna(product_row[img_col_name]):
            image_ok, status_code = check_image_status(product_row[img_col_name])
            col1, col2 = st.columns(2)
            with col1:
                st.image(product_row[img_col_name], use_column_width=True)
            with col2:
                st.write(f"SKU: {sku}\n\n{img_col_name}")

                if not image_ok and status_code is not None:
                    st.error(f"Image URL broken ({status_code})")

                # Determine checkbox value based on batch option
                if batch_option == "Tick All":
                    checkbox_value = True
                elif batch_option == "Tick All Except Broken Images":
                    checkbox_value = image_ok
                elif batch_option == "None":
                    checkbox_value = False
                else:  # By default, checkbox reflects individual image status
                    checkbox_value = image_ok

                st.checkbox("Image OK?", value=checkbox_value, key=f"{sku}_{idx}")




def main():
    st.title("Product Image Viewer")
    uploaded_file = st.file_uploader("Upload your spreadsheet", type=["csv", "xlsx"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

        # Introducing the batch selection options using st.radio
        batch_option = st.radio("Batch Selection Option:", ["None", "Tick All", "Tick All Except Broken Images"])

        with st.form("image_review_form"):
            total_rows = len(df)
            progress_bar = st.progress(0)

            for idx, row in enumerate(df.iterrows()):
                _, row = row
                display_product_card(row, batch_option)
                st.write("---")

                progress_bar.progress((idx + 1) / total_rows)

            progress_bar.empty()
            if st.form_submit_button("Submit Reviews"):
                # Create a new column to store the checkbox results
                df['Image Check'] = df.apply(lambda row: "|".join(
                    ["OK" if st.session_state.get(f"{row['SKU']}_{i}", True) else "Not OK" for i in range(1, 6)]),
                                             axis=1)

                # Generate a download link for the modified dataframe
                st.markdown(get_table_download_link(df), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
