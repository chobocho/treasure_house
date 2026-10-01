// 슬라이드 p3-v2-invariance — 배열은 공변, C# 2.0
using System;

class App
{
    static void Main()
    {
        string[] names = new string[] { "a" };
        object[] objs = names;            // arrays: covariant
        try
        {
            objs[0] = 42;                 // so every store is checked
        }
        catch (ArrayTypeMismatchException e)
        {
            Console.WriteLine(e.GetType().Name);
        }
    }
}
