// 슬라이드 p15-v14-xm-ambig — 모호함과 구현 메서드로 고르기, C# 14
using System;

static class E1
{
    extension(object o)
    {
        public static string M() => "E1.M";
        public string M2() => "E1.M2";
        public int P => 1;
    }
}

static class E2
{
    extension(object o)
    {
        public static string M() => "E2.M";
        public string M2() => "E2.M2";
        public int P => 2;
    }
}

class Program
{
    static void Main()
    {
        object x = new object();
        Console.WriteLine(E1.M() + " " + E2.M());            // static
        Console.WriteLine(E1.M2(x) + " " + E2.M2(x));        // instance
        Console.WriteLine(E1.get_P(x) + " " + E2.get_P(x));  // property
#if A1
        Console.WriteLine(object.M());
#elif A2
        Console.WriteLine(x.M2());
#elif A3
        Console.WriteLine(x.P);
#endif
    }
}
