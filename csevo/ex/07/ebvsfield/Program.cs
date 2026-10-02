// 슬라이드 p7-v6-eb-vsfield — = 와 => 한 글자 차이, C# 6.0
using System;
using System.Reflection;

class Config
{
    public int A = 5;                   // field, initialized once
    public int B => 5;                  // property, getter returns 5
    public Func<int> C = () => 5;       // field of delegate type
}

class Program
{
    static void Show(string name)
    {
        MemberInfo m = typeof(Config).GetMember(name)[0];
        Console.WriteLine(name + ": " + m.MemberType);
    }

    static void Main()
    {
        Show("A");
        Show("B");
        Show("C");
        Config c = new Config();
        Console.WriteLine(c.A + " " + c.B + " " + c.C());
    }
}
