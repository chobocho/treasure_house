// 슬라이드 p5-v4-dyn-compound — 복합 대입의 평가 차례, C# 4.0
using System;

class Box
{
    int value;
    public int Property
    {
        get { Console.WriteLine("  get_Property"); return value; }
        set { Console.WriteLine("  set_Property"); this.value = value; }
    }
}

class Program
{
    static dynamic GetDynamic()
    {
        Console.WriteLine("  GetDynamic()");
        return new Box();
    }

    static int GetInt()
    {
        Console.WriteLine("  GetInt()");
        return 1;
    }

    static void Main()
    {
        Console.WriteLine("GetDynamic().Property += GetInt();");
        GetDynamic().Property += GetInt();
    }
}
