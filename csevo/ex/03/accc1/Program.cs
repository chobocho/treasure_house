// 슬라이드 p3-v2-accessor-why — 읽기는 공개, 쓰기는 안에서만 — C# 1.0
using System;

class Account
{
    int balance;

    public int Balance                   // get only: read-only outside
    {
        get { return balance; }
    }

    void SetBalance(int value)           // writing needs another name
    {
        if (value < 0) throw new ArgumentException("negative");
        balance = value;
    }

    public void Deposit(int amount) { SetBalance(balance + amount); }
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
