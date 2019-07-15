# Trello-Analyzer

Trello-Analyzer is a workload statistics tool, can autamtically achieve analysis and vistualization and email notification. 

## Process Management

### 需求：
- 1. 数据清理和统计
    - 正则表达式能否判定，需要修改，用了 split 来统计
    - list name 需要判定方式修改
    - 统计出个人在每一个 list 上的工作时间，需要理清那些 hours 的逻辑
    - save json 和完成新增卡片的统计
- 2. 时间段统计，通过直接输入日期，然后拿到从那个时间开始到现在的所有工作时间统计

### 流程：
- 1. 单个 list 的统计、可视化：研究是用之前作图的脚本还是自己写
- 2. 定时任务，每周五晚
- 3. 模块化脚本、自动邮件等
- 4. 【】统计


### 进度管理
#### 进度 0601
- 1. 修复正则对 [] 判断，拿到 list_id
- 2. 换了一种统计 actual hours 的方式
- 3. cardinfo_turn_to_dict 函数，save json 还没弄
- 4. 统计一个 list 中每个人的工作时长（单周统计）

#### 进度 0606 
- 1. 时间段统计 finished
- 2. 抽样数据检查，抽几周试一下
- 3. 修复了一点 bug，可以适用于 thunderDB 

#### 进度 0612
- 1. 加入了最新一周的统计
- 2. 可视化
