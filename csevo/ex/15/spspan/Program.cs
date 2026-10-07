// 슬라이드 p15-v14-sp-span — 쓸 수 있는 Span 에는 공변이 없다, C# 14
using System;

class Program
{
    static void Main()
    {
        string[] words = ["a", "b"];
        try
        {
#if CAST
            Span<object> s = (Span<object>)words;  // explicit
#else
            Span<object> s = words;    // C# 13: user-defined operator
#endif
            s[0] = 42;                 // would put an int in string[]
            Console.WriteLine(words[0]);
        }
        catch (ArrayTypeMismatchException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
