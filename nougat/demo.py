from nougat import NougatModel

model = NougatModel()  # 加载默认配置的模型
image_path = '/data1/nzw/data/pdf_parser/publaynet/train/PMC514717_00001.jpg'  # 更改为你的文件路径
output = model.predict(image_path)
print(output)