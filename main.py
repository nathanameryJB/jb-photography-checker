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



def display_product_card(product_row):
    # Extract values from the product row
    sku, product_name = product_row['SKU'], product_row['Product Name']

    # Display the SKU and Product Name with SKU being smaller
    st.markdown(f"## {sku}", unsafe_allow_html=True)
    st.markdown(f"{product_name}")

    # Display images related to the product (up to 5) along with checkboxes
    for idx in range(1, 6):
        img_col_name = f"Image {idx}"

        if pd.notna(product_row[img_col_name]):
            # Check the image URL status
            image_ok, status_code = check_image_status(product_row[img_col_name])

            # Using columns to position image and checkbox side by side
            col1, col2 = st.columns(2)
            with col1:
                st.image(product_row[img_col_name], use_column_width=True)
            with col2:
                st.write(f"SKU: {sku} | {img_col_name}")  # Display SKU and image number

                # If image is not OK, show an error message
                if not image_ok and status_code is not None:
                    st.error(f"Image URL broken ({status_code})")

                st.checkbox("Image OK?", value=image_ok, key=f"{sku}_{idx}")

def get_table_download_link(df):
    """Generates a link to download the dataframe in csv format"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="reviews.csv">Download CSV File</a>'



def main():
    st.title("Product Image Viewer")

    st.write("This app is designed to take a spreadsheet of images with the following columns:")

    st.markdown("""
    | SKU | Product Name | Batch | Website Y/N | Image 1 | Image 2 | Image 3 | Image 4 | Image 5 |
    |-----|--------------|-------|-------------|---------|---------|---------|---------|---------|
    """)

    st.write(
        "It will then display the images for checking below, allowing you to untick the checkbox if the image is not right. At the same time, it will check for broken images in the list and automatically untick the checkbox. At the bottom of the list, you can submit the image checks, then you will be able to download the results as a csv")

    uploaded_file = st.file_uploader("Upload your spreadsheet", type=["csv", "xlsx"])

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')

        # Start the form here
        with st.form("image_review_form"):
            # Progress bar setup
            total_rows = len(df)
            progress_bar = st.progress(0)

            # Display products in a card format
            for idx, row in enumerate(df.iterrows()):
                _, row = row
                display_product_card(row)
                st.write("---")  # separator between cards

                # Update progress bar
                progress_bar.progress((idx + 1) / total_rows)

            progress_bar.empty()

            required_columns = ["SKU", "Product Name", "Image 1", "Image 2", "Image 3", "Image 4", "Image 5"]
            if not all(col in df.columns for col in required_columns):
                st.error("The uploaded spreadsheet might be missing some required columns.")
            else:
                # Submit button
                if st.form_submit_button("Submit Image Checks"):
                    # Create a new column to store the checkbox results
                    df['Image Check'] = df.apply(lambda row: "|".join(["OK" if st.session_state.get(f"{row['SKU']}_{i}", True) else "Not OK" for i in range(1, 6)]), axis=1)

                    # Generate a download link for the modified dataframe
                    st.markdown(get_table_download_link(df), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
