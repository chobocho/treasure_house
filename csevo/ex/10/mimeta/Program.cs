// 슬라이드 p10-v9-mi-meta — 모듈 초기화자가 들어가는 자리, C# 9.0
using System;
using System.IO;
using System.Reflection;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Runtime.CompilerServices;

static class Gen
{
    [ModuleInitializer] internal static void First() { }
    [ModuleInitializer] internal static void Second() { }
}

class App
{
    static void Main()
    {
        Module mod = typeof(App).Module;
        string path = mod.Assembly.Location;
        using var pe = new PEReader(File.OpenRead(path));
        MetadataReader md = pe.GetMetadataReader();
        foreach (TypeDefinitionHandle th in md.TypeDefinitions)
        {
            TypeDefinition t = md.GetTypeDefinition(th);
            foreach (MethodDefinitionHandle mh in t.GetMethods())
            {
                MethodDefinition m = md.GetMethodDefinition(mh);
                string name = md.GetString(m.Name);
                if (md.GetString(t.Name) != "<Module>") continue;
                byte[] il = pe.GetMethodBody(m.RelativeVirtualAddress)
                              .GetILBytes();
                Console.WriteLine("<Module>." + name + " IL: "
                                  + BitConverter.ToString(il));
                for (int i = 0; i + 4 < il.Length; i += 5)  // call tok
                    Console.WriteLine("  call " + mod.ResolveMethod(
                        BitConverter.ToInt32(il, i + 1)).Name);
            }
        }
    }
}
