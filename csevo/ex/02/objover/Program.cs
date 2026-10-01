// 슬라이드 p2-v1-objover — object 의 세 메서드를 함께 재정의, C# 1.0
using System;
using System.Collections;

class Money
{
    readonly string cur;
    readonly long cents;
    public Money(string c, long n) { cur = c; cents = n; }

    public override string ToString()
    {
        string frac = (cents % 100).ToString("00");
        return cur + " " + cents / 100 + "." + frac;
    }

    public override bool Equals(object o)
    {
        Money m = o as Money;
        return m != null && m.cur == cur && m.cents == cents;
    }

    public override int GetHashCode()
    {
        return (int)cents ^ cur.Length;   // equal objects, equal hashes
    }
}

class App
{
    static void Main()
    {
        Hashtable price = new Hashtable();
        price[new Money("KRW", 150000)] = "coffee";
        Money key = new Money("KRW", 150000);   // a different object
        Money same = new Money("KRW", 150000);
        Console.WriteLine("key:    " + key);
        Console.WriteLine("Equals: " + key.Equals(same));
        Console.WriteLine("==:     " + (key == same));
        Console.WriteLine("lookup: " + price[key]);
    }
}
