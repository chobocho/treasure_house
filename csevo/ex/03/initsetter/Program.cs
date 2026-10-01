// 슬라이드 p3-v2-accessor-later — init 접근자, C# 9
using System;

class Account
{
    public int Id { get; init; }         // set only while creating
    public int Balance { get; private set; }
}

class App
{
    static void Main()
    {
        Account a = new Account { Id = 7 };
        Console.WriteLine(a.Id + " " + a.Balance);
    }
}
