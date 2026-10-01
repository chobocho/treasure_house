// 슬라이드 p4-v3-ext-private — 남의 private 은 못 본다, C# 3.0
using System;

class Account
{
    int balance = 100;
    public int Visible = 1;
}

static class AccountExt
{
    public static int Peek(this Account a) { return a.balance; }
    public static int Ok(this Account a) { return a.Visible; }
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Account().Peek());
    }
}
