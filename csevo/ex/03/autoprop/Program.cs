// 슬라이드 p3-v2-accessor-later — 자동 속성과 private set, C# 3.0
using System;

class Account
{
    public int Balance { get; private set; }
    public void Deposit(int amount) { Balance += amount; }
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
