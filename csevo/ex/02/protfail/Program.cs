// 슬라이드 p2-v1-protfail — protected 는 "내 쪽" 참조로만, C# 1.0
class Account
{
    protected decimal balance;
}

class Savings : Account
{
    public void Copy(Savings s, Account a)
    {
        balance = s.balance;        // fine: through a Savings
        balance = a.balance;        // not through a plain Account
    }
}

class App
{
    static void Main() { }
}
