// 슬라이드 p3-v2-accessor-gate — 접근자마다 다른 접근 수준, C# 2.0
using System;

class Account
{
    int balance;

    public int Balance
    {
        get { return balance; }
        private set                      // one property, two levels
        {
            if (value < 0) throw new ArgumentException("negative");
            balance = value;
        }
    }

    public void Deposit(int amount) { Balance = Balance + amount; }
}

class App
{
    static void Main()
    {
        Account a = new Account();
        a.Deposit(30);
        Console.WriteLine(a.Balance);
    }
}
