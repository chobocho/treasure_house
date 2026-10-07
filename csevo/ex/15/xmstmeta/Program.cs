// 슬라이드 p15-v14-xm-static-meta — 정적 확장 멤버의 구현 메서드, C# 14
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

static class ListExt
{
    extension<T>(List<T>)
    {
        public static List<T> Of(params T[] items) => new(items);
        public static int Made => 1;
    }

    extension<T>(List<T> list)
    {
        public T Head => list[0];
    }
}

class Program
{
    static void Main()
    {
        foreach (MethodInfo m in typeof(ListExt).GetMethods(
            BindingFlags.Public | BindingFlags.Static
            | BindingFlags.DeclaredOnly).OrderBy(m => m.Name))
            Console.WriteLine(m + "  [Extension]="
                + m.IsDefined(typeof(ExtensionAttribute)));
        Console.WriteLine(ListExt.get_Made<string>()
            + " " + ListExt.get_Head(List<int>.Of(7, 8)));
    }
}
