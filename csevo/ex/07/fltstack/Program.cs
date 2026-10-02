// 슬라이드 p7-v6-filter-stack — 필터 안에서 본 호출 스택, C# 6.0
using System;
using System.Diagnostics;
using System.Linq;

class Program
{
    static bool InnerOnStack(string where)
    {
        bool on = new StackTrace().GetFrames()
            .Any(f => f.GetMethod().Name == "Inner");
        Console.WriteLine(where + ": Inner on stack = " + on);
        return true;
    }

    static void Inner()
    {
        throw new InvalidOperationException();
    }

    static void Main()
    {
        try
        {
            Inner();
        }
        catch (Exception) when (InnerOnStack("filter"))
        {
            InnerOnStack("catch body");
        }
    }
}
