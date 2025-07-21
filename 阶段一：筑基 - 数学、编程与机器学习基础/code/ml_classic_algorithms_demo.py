# 机器学习经典算法实现与可视化
# 作者：xxx
# 说明：本脚本演示常见机器学习算法的原理、实现与可视化，适合教学和自学参考。
# 算法包括：线性回归、逻辑回归、支持向量机、决策树、随机森林、梯度提升树、K-Means聚类、主成分分析

import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.datasets import make_classification, make_blobs, make_regression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error

# =========================
# 1. 线性回归 Linear Regression
# =========================
# 原理说明：
# 线性回归用于拟合输入特征与输出变量之间的线性关系，目标是最小化预测值与真实值之间的均方误差。
# 适用于回归问题。
def demo_linear_regression():
    # 生成一组一维回归数据
    X, y = make_regression(n_samples=100, n_features=1, noise=15, random_state=0)
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    # 可视化
    plt.figure(figsize=(6,4))
    plt.rcParams["font.sans-serif"] = "SimHei"
    plt.rcParams["axes.unicode_minus"] = False
    plt.scatter(X, y, color='blue', label='真实数据')
    plt.plot(X, y_pred, color='red', label='预测直线')
    plt.title('线性回归示例')
    plt.xlabel('X')
    plt.ylabel('y')
    plt.legend()
    plt.show()
    print(f'均方误差: {mean_squared_error(y, y_pred):.2f}')

# =========================
# 2. 逻辑回归 Logistic Regression
# =========================
# 原理说明：
# 逻辑回归用于二分类问题，通过sigmoid函数将线性组合映射到0-1区间，输出概率。
# 适用于分类问题。
def demo_logistic_regression():
    # 生成二维可分数据
    X, y = make_classification(n_samples=100, n_features=2, n_redundant=0, n_clusters_per_class=1, random_state=1)
    model = LogisticRegression()
    model.fit(X, y)
    # 可视化决策边界
    plt.figure(figsize=(6,4))
    plt.rcParams["font.sans-serif"] = "SimHei"
    plt.rcParams["axes.unicode_minus"] = False
    plt.scatter(X[:,0], X[:,1], c=y, cmap='bwr', edgecolor='k', label='样本点')
    # 绘制决策边界
    xx, yy = np.meshgrid(np.linspace(X[:,0].min()-1, X[:,0].max()+1, 100),
                         np.linspace(X[:,1].min()-1, X[:,1].max()+1, 100))
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    plt.contourf(xx, yy, Z, alpha=0.2, cmap='bwr')
    plt.title('逻辑回归决策边界')
    plt.xlabel('X1')
    plt.ylabel('X2')
    plt.show()
    print(f'分类准确率: {accuracy_score(y, model.predict(X)):.2f}')

# =========================
# 3. 支持向量机 SVM
# =========================
# 原理说明：
# 支持向量机通过最大化类别间隔实现最优分类，支持线性和非线性核函数。
# 适用于分类问题。
def demo_svm():
    X, y = make_classification(n_samples=100, n_features=2, n_redundant=0, n_clusters_per_class=1, random_state=2)
    model = SVC(kernel='linear')
    model.fit(X, y)
    plt.figure(figsize=(6,4))
    plt.rcParams["font.sans-serif"] = "SimHei"
    plt.rcParams["axes.unicode_minus"] = False
    plt.scatter(X[:,0], X[:,1], c=y, cmap='bwr', edgecolor='k')
    # 绘制决策边界
    xx, yy = np.meshgrid(np.linspace(X[:,0].min()-1, X[:,0].max()+1, 100),
                         np.linspace(X[:,1].min()-1, X[:,1].max()+1, 100))
    Z = model.decision_function(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    plt.contour(xx, yy, Z, levels=[0], linewidths=2, colors='black')
    plt.title('支持向量机决策边界')
    plt.xlabel('X1')
    plt.ylabel('X2')
    plt.show()
    print(f'分类准确率: {accuracy_score(y, model.predict(X)):.2f}')

# =========================
# 4. 决策树 Decision Tree
# =========================
# 原理说明：
# 决策树通过特征划分将数据递归分割，形成树结构，适用于分类和回归。
def demo_decision_tree():
    X, y = make_classification(n_samples=100, n_features=2, n_redundant=0, n_clusters_per_class=1, random_state=3)
    model = DecisionTreeClassifier(max_depth=3)
    model.fit(X, y)
    plt.figure(figsize=(6,4))
    plt.rcParams["font.sans-serif"] = "SimHei"
    plt.rcParams["axes.unicode_minus"] = False
    plt.scatter(X[:,0], X[:,1], c=y, cmap='bwr', edgecolor='k')
    xx, yy = np.meshgrid(np.linspace(X[:,0].min()-1, X[:,0].max()+1, 100),
                         np.linspace(X[:,1].min()-1, X[:,1].max()+1, 100))
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    plt.contourf(xx, yy, Z, alpha=0.2, cmap='bwr')
    plt.title('决策树决策边界')
    plt.xlabel('X1')
    plt.ylabel('X2')
    plt.show()
    print(f'分类准确率: {accuracy_score(y, model.predict(X)):.2f}')

# =========================
# 5. 随机森林 Random Forest
# =========================
# 原理说明：
# 随机森林集成多棵决策树，通过投票或平均提升泛化能力，减少过拟合。
def demo_random_forest():
    X, y = make_classification(n_samples=100, n_features=2, n_redundant=0, n_clusters_per_class=1, random_state=4)
    model = RandomForestClassifier(n_estimators=20, max_depth=3)
    model.fit(X, y)
    plt.figure(figsize=(6,4))
    plt.rcParams["font.sans-serif"] = "SimHei"
    plt.rcParams["axes.unicode_minus"] = False
    plt.scatter(X[:,0], X[:,1], c=y, cmap='bwr', edgecolor='k')
    xx, yy = np.meshgrid(np.linspace(X[:,0].min()-1, X[:,0].max()+1, 100),
                         np.linspace(X[:,1].min()-1, X[:,1].max()+1, 100))
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    plt.contourf(xx, yy, Z, alpha=0.2, cmap='bwr')
    plt.title('随机森林决策边界')
    plt.xlabel('X1')
    plt.ylabel('X2')
    plt.show()
    print(f'分类准确率: {accuracy_score(y, model.predict(X)):.2f}')

# =========================
# 6. 梯度提升树 Gradient Boosting
# =========================
# 原理说明：
# 梯度提升树通过多棵弱分类器（如决策树）逐步拟合残差，提升整体性能。
def demo_gradient_boosting():
    X, y = make_classification(n_samples=100, n_features=2, n_redundant=0, n_clusters_per_class=1, random_state=5)
    model = GradientBoostingClassifier(n_estimators=20, max_depth=3)
    model.fit(X, y)
    plt.figure(figsize=(6,4))
    plt.rcParams["font.sans-serif"] = "SimHei"
    plt.rcParams["axes.unicode_minus"] = False
    plt.scatter(X[:,0], X[:,1], c=y, cmap='bwr', edgecolor='k')
    xx, yy = np.meshgrid(np.linspace(X[:,0].min()-1, X[:,0].max()+1, 100),
                         np.linspace(X[:,1].min()-1, X[:,1].max()+1, 100))
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    plt.contourf(xx, yy, Z, alpha=0.2, cmap='bwr')
    plt.title('梯度提升树决策边界')
    plt.xlabel('X1')
    plt.ylabel('X2')
    plt.show()
    print(f'分类准确率: {accuracy_score(y, model.predict(X)):.2f}')

# =========================
# 7. K-Means聚类 K-Means Clustering
# =========================
# 原理说明：
# K-Means是一种无监督聚类算法，通过迭代将样本分配到最近的质心，更新质心位置，直到收敛。
def demo_kmeans():
    X, y_true = make_blobs(n_samples=100, centers=3, n_features=2, random_state=6)
    model = KMeans(n_clusters=3, random_state=6)
    y_pred = model.fit_predict(X)
    plt.figure(figsize=(6,4))
    plt.rcParams["font.sans-serif"] = "SimHei"
    plt.rcParams["axes.unicode_minus"] = False
    plt.scatter(X[:,0], X[:,1], c=y_pred, cmap='viridis', edgecolor='k')
    plt.scatter(model.cluster_centers_[:,0], model.cluster_centers_[:,1], s=200, c='red', marker='X', label='质心')
    plt.title('K-Means聚类结果')
    plt.xlabel('X1')
    plt.ylabel('X2')
    plt.legend()
    plt.show()

# =========================
# 8. 主成分分析 PCA
# =========================
# 原理说明：
# 主成分分析是一种降维方法，通过线性变换将高维数据投影到方差最大的方向上，实现数据压缩和可视化。
def demo_pca():
    X, _ = make_blobs(n_samples=100, centers=3, n_features=3, random_state=7)
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)
    plt.figure(figsize=(6,4))
    plt.rcParams["font.sans-serif"] = "SimHei"
    plt.rcParams["axes.unicode_minus"] = False
    plt.scatter(X_pca[:,0], X_pca[:,1], c='b', edgecolor='k')
    plt.title('主成分分析（PCA）降维结果')
    plt.xlabel('主成分1')
    plt.ylabel('主成分2')
    plt.show()
    print('各主成分方差占比:', pca.explained_variance_ratio_)

# =========================
# 主程序入口
# =========================
if __name__ == '__main__':
    print('1. 线性回归')
    demo_linear_regression()
    print('\n2. 逻辑回归')
    demo_logistic_regression()
    print('\n3. 支持向量机')
    demo_svm()
    print('\n4. 决策树')
    demo_decision_tree()
    print('\n5. 随机森林')
    demo_random_forest()
    print('\n6. 梯度提升树')
    demo_gradient_boosting()
    print('\n7. K-Means聚类')
    demo_kmeans()
    print('\n8. 主成分分析')
    demo_pca() 