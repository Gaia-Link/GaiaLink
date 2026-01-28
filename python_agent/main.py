"""
Gaia Link Agent - 主程式入口

展示如何使用基於 SpoonOS 的 Gaia Link Agent
"""

import asyncio
from dotenv import load_dotenv

from gaia_link import GaiaLinkAgent
from gaia_link.tools import (
    VerifyCrisisTool,
    AnalyzeSentimentTool,
    ExecuteDonationTool,
)

# 載入環境變數
load_dotenv()


async def demo_verify_crisis():
    """展示 verify_crisis 工具"""
    print("\n" + "=" * 60)
    print("[Demo] verify_crisis (驗證危機)")
    print("=" * 60)

    tool = VerifyCrisisTool()

    # 測試土耳其地震區域
    print("\n[Test] 測試土耳其地震區域 (lat=37.5, long=37.0):")
    result = await tool.execute(lat=37.5, long=37.0)
    print(f"   狀態: {result['status']}")
    print(f"   可信度: {result['confidence']}%")
    print(f"   相關事件: {len(result['polymarket_events'])} 個")
    for event in result['polymarket_events']:
        print(f"      - {event['title']} (機率: {event['probability']*100:.0f}%)")

    # 測試未知區域
    print("\n[Test] 測試未知區域 (lat=-80.0, long=0.0):")
    result = await tool.execute(lat=-80.0, long=0.0)
    print(f"   狀態: {result['status']}")
    print(f"   可信度: {result['confidence']}%")
    print(f"   風險因素: {len(result['risk_factors'])} 個")


async def demo_analyze_sentiment():
    """展示 analyze_sentiment 工具"""
    print("\n" + "=" * 60)
    print("[Demo] analyze_sentiment (情感分析)")
    print("=" * 60)

    tool = AnalyzeSentimentTool()

    # 測試緊急求救文本
    print("\n[Test] 測試緊急求救文本:")
    urgent_text = "Please help! My house is on fire, people are trapped inside! We need rescue immediately!"
    result = await tool.execute(text=urgent_text)
    print(f"   緊急程度: {result['urgency_level']}")
    print(f"   真實性分數: {result['authenticity_score']}%")
    print(f"   情緒指標: {result['emotional_indicators']}")

    # 測試詐騙文本
    print("\n[Test] 測試詐騙文本:")
    scam_text = "URGENT: Send money NOW to this crypto wallet! Only 24 hours left! 1000% guaranteed return!"
    result = await tool.execute(text=scam_text)
    print(f"   緊急程度: {result['urgency_level']}")
    print(f"   真實性分數: {result['authenticity_score']}%")
    print(f"   紅旗警告: {result['red_flags']}")


async def demo_execute_donation():
    """展示 execute_donation 工具"""
    print("\n" + "=" * 60)
    print("[Demo] execute_donation (執行捐款)")
    print("=" * 60)

    tool = ExecuteDonationTool()

    # 測試成功的捐款
    print("\n[Test] 測試成功的 USDC 捐款:")
    result = await tool.execute(
        amount=100.0,
        token="USDC",
        recipient_address="0x1234567890abcdef1234567890abcdef12345678"
    )
    print(f"   成功: {result['success']}")
    print(f"   交易 ID: {result['transaction_id'][:20]}...")
    print(f"   狀態: {result['status']}")
    if result['details']:
        print(f"   金額: {result['details']['amount_sent']} {result['details']['token']}")
        print(f"   Gas 費: {result['details']['gas_fee']} ETH")
        print(f"   總成本: ${result['details']['total_cost_usd']} USD")

    # 測試失敗的捐款（無效地址）
    print("\n[Test] 測試失敗的捐款（無效地址）:")
    result = await tool.execute(
        amount=50.0,
        token="ETH",
        recipient_address="invalid_address"
    )
    print(f"   成功: {result['success']}")
    print(f"   錯誤: {result['error']}")


async def demo_agent_info():
    """展示 Agent 資訊"""
    print("\n" + "=" * 60)
    print("[Demo] GaiaLinkAgent (Agent 資訊)")
    print("=" * 60)

    agent = GaiaLinkAgent()
    info = agent.get_info()

    print(f"\n   名稱: {info['name']}")
    print(f"   描述: {info['description'][:60]}...")
    print(f"   工具數量: {len(info['tools'])}")
    print(f"   註冊工具: {', '.join(info['tools'])}")
    print(f"   最大步數: {info['max_steps']}")


async def main():
    """主程式"""
    print("\n" + "=" * 60)
    print("Gaia Link Agent - SpoonOS Demo")
    print("=" * 60)
    print("\n此 Agent 基於 SpoonOS React Agent 架構")
    print("符合 SpoonOS Hackathon 最低技術要求\n")

    # 運行所有 Demo
    await demo_agent_info()
    await demo_verify_crisis()
    await demo_analyze_sentiment()
    await demo_execute_donation()

    print("\n" + "=" * 60)
    print("[OK] Demo 完成！")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
