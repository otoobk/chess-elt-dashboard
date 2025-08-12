from pyspark.sql import SparkSession

"""
Gets or creates SparkSession for an app
"""
def get_spark_session(app_name: str = "SparkApp"):
    spark = (
        SparkSession.builder
        .appName(app_name)
        .config("spark.executor.memory", "4g")
        .config("spark.driver.memory", "4g")
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.sql.shuffle.partitions", "16")
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    
    return spark

"""
Stops SparkSession
"""
def stop_spark_session(spark: SparkSession):
    spark.stop()