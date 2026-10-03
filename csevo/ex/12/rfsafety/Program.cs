// 슬라이드 p12-v11-rf-safety — 모듈에 붙는 RefSafetyRules, C# 11
using System;
using System.Reflection;

class Program
{
    static void Main()
    {
        Module m = typeof(Program).Module;
        foreach (CustomAttributeData a in m.GetCustomAttributesData())
        {
            Console.Write(a.AttributeType.Name);
            foreach (CustomAttributeTypedArgument x
                     in a.ConstructorArguments)
                Console.Write(" " + x.Value);
            Console.WriteLine();
        }
    }
}
