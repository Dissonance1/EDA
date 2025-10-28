# 🚀 Automated EDA (Exploratory Data Analysis) Web Application

A powerful, interactive web application built with Streamlit that automates the process of Exploratory Data Analysis (EDA). This tool provides comprehensive data insights through interactive visualizations and automated statistical analysis.

## ✨ Features

### 📊 **Dataset Overview Tab**
- **Basic Statistics**: Rows, duplicates, features count
- **Column Classification**: Automatic separation of continuous and categorical columns
- **Correlation Analysis**: Interactive correlation heatmaps for numerical features
- **Missing Values**: Visual representation of missing data patterns

### 📈 **Individual Column Stats Tab**
- **Continuous Features**: 
  - Descriptive statistics (mean, std, min, max, quantiles)
  - Interactive histograms with Plotly
  - Missing value analysis
- **Categorical Features**: 
  - Value distribution charts
  - Frequency analysis

### 🔍 **Feature Relationships Tab**
- **Scatter Plots**: Interactive scatter plots between continuous variables
- **Color Encoding**: Option to color-code points by categorical variables
- **Dynamic Selection**: Choose X and Y axes from available features

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Matplotlib, Missingno
- **Language**: Python 3.13+

## 📋 Prerequisites

- Python 3.13 or higher
- pip (Python package installer)

## 🚀 Installation & Setup

### 1. Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd EDA

# Or simply download and extract the project files
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Or install manually:**
```bash
pip install streamlit pandas plotly matplotlib missingno
```

### 3. Run the Application
```bash
python -m streamlit run python_eda_app.py
```

The app will open automatically in your default web browser at `http://localhost:8501`

## 📁 Project Structure

```
EDA/
├── python_eda_app.py      # Main application file
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── sample_data/           # Optional: Add sample datasets here
```

## 🎯 How to Use

### 1. **Upload Your Data**
- Click "Browse files" to upload a CSV file
- The app supports standard CSV format
- Ensure your data has both continuous and categorical columns for best results

### 2. **Navigate Through Tabs**
- **Dataset Overview**: Get a bird's eye view of your data
- **Individual Column Stats**: Dive deep into specific features
- **Feature Relationships**: Explore correlations and patterns

### 3. **Interactive Features**
- Use dropdown menus to select different features
- Hover over charts for detailed information
- Zoom and pan through visualizations
- Download charts (if supported by your browser)

## 📊 Sample Datasets

For testing, you can use popular datasets like:
- **Titanic Dataset**: [Download from Kaggle](https://www.kaggle.com/competitions/titanic/data?select=train.csv)
- **Iris Dataset**: Built into many data science libraries
- **Boston Housing Dataset**: Available in scikit-learn

## 🔧 Troubleshooting

### Common Issues:

1. **Port Already in Use**
   ```bash
   python -m streamlit run python_eda_app.py --server.port 8502
   ```

2. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.13+ recommended)

3. **Memory Issues with Large Datasets**
   - Consider sampling your data for initial exploration
   - Use data types optimization (e.g., `category` for categorical columns)

### Error: "module 'numpy' has no attribute 'bool8'"
This is a compatibility issue with Python 3.13 and older packages. The app has been updated to use Plotly instead of Bokeh to resolve this.

## 🌟 Key Benefits

- **No Coding Required**: Upload data and get instant insights
- **Interactive Visualizations**: Modern, responsive charts
- **Automated Analysis**: Saves hours of manual EDA work
- **Professional Output**: Publication-ready visualizations
- **User-Friendly**: Intuitive interface for data scientists and analysts

## 📚 Learning Resources

- **Streamlit Documentation**: [https://docs.streamlit.io/](https://docs.streamlit.io/)
- **Plotly Documentation**: [https://plotly.com/python/](https://plotly.com/python/)
- **Pandas Documentation**: [https://pandas.pydata.org/](https://pandas.pydata.org/)

## 🤝 Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Improving documentation
- Adding new visualization types

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built with Streamlit for the web interface
- Powered by Plotly for interactive visualizations
- Enhanced with Pandas for data manipulation
- Styled with modern web technologies

---

**Happy Data Exploring! 🎉**

*For support or questions, please open an issue in the project repository.*
