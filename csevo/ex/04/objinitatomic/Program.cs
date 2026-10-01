// 슬라이드 p4-v3-objinit-atomic — 반쯤 만든 객체는 안 닿는다, C# 3.0
using System;

class Account
{
    public string Owner;
    public int Balance;
}

class App
{
    static int Fail()
    {
        throw new InvalidOperationException("no balance");
    }

    static void Main()
    {
        Account acc = new Account { Owner = "old", Balance = 1 };
        try
        {
            acc = new Account { Owner = "new", Balance = Fail() };
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine("caught: " + e.Message);
        }
        Console.WriteLine(acc.Owner + " " + acc.Balance);
    }
}
