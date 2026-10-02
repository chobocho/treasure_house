// 슬라이드 p7-v6-eb-throw — => throw 는 C# 7.0, C# 7.0
using System;

class Account
{
    public void Close()
        => throw new InvalidOperationException("closed");
}

class Program
{
    static void Main()
    {
        try
        {
            new Account().Close();
        }
        catch (InvalidOperationException e)
        {
            Console.WriteLine(e.Message);
        }
    }
}
