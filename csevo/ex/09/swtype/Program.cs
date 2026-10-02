// 슬라이드 p9-v8-switchexpr-type — switch 식의 형식, C# 8.0
using System;

class App
{
    static void Main()
    {
        bool f = false;
        // best common type of the arms: int and double -> double
        var a = f switch { true => 1, false => 2.5 };
        // an arm without a type (null) takes the other arms' type
        var b = f switch { true => "yes", false => null };
        // no common type, but a target type exists -> converts
        object c = f switch { true => 1, false => "one" };
        Console.WriteLine("{0} {1}", a.GetType().Name, a);
        Console.WriteLine("{0}", b == null ? "null string" : b);
        Console.WriteLine("{0} {1}", c.GetType().Name, c);
#if BAD
        var d = f switch { true => 1, false => "one" };
#endif
    }
}
