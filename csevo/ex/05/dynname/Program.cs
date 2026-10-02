// 슬라이드 p5-v4-dyn-name — dynamic 은 키워드가 아니다, C# 4.0
using System;

class dynamic
{
    public override string ToString()
    {
        return "my own class named dynamic";
    }
}

class Program
{
    static void Main()
    {
        dynamic d = new dynamic();
        Console.WriteLine(d);
        Console.WriteLine(d.GetType());
    }
}
