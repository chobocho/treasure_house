// 슬라이드 p2-v1-paramir — 메타데이터 속의 ref·out·params, C# 1.0
using System;
using System.Reflection;

class App
{
    static void M(int v, ref int r, out int o, params int[] rest)
    {
        o = v + r + rest.Length;
    }

    static void Main()
    {
        MethodInfo m = typeof(App).GetMethod("M",
            BindingFlags.NonPublic | BindingFlags.Static);
        ParameterInfo[] ps = m.GetParameters();
        foreach (ParameterInfo p in ps)
        {
            bool pa = p.IsDefined(typeof(ParamArrayAttribute), false);
            Console.WriteLine(p.Name + ": " + p.ParameterType.Name
                + " out=" + p.IsOut + " ParamArray=" + pa);
        }
    }
}
